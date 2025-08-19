from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.utils import secure_filename
import os
import pandas as pd
from datetime import datetime, timedelta
import logging
import json
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import urllib.parse
import shutil
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/webapp.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a random secret key

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv', 'txt'}

# Global variables for message sending status
message_status = {
    'is_running': False,
    'current_step': '',
    'progress': 0,
    'total': 0,
    'messages': []
}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_upload_dirs():
    """Create necessary upload directories"""
    dirs = ['uploads', 'templates', 'logs']
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)

def initialize_default_configs():
    """Initialize default configuration files if they don't exist"""
    
    # Create default config.json if it doesn't exist
    if not os.path.exists('config.json'):
        if os.path.exists('default_config.json'):
            import shutil
            shutil.copy('default_config.json', 'config.json')
            logging.info("Created config.json from defaults")
        else:
            # Fallback default config
            default_config = {
                "notification_contact1": "+919876543210",
                "notification_contact2": "+918765432109", 
                "user_data_type": "shs"
            }
            with open('config.json', 'w') as f:
                json.dump(default_config, f, indent=2)
            logging.info("Created default config.json")
    
    # Create default message templates if they don't exist
    template_files = {
        'active_message.txt': 'default_templates/active_message.txt',
        'inactive_message.txt': 'default_templates/inactive_message.txt', 
        'no_instruction_message.txt': 'default_templates/no_instruction_message.txt'
    }
    
    for template_file, default_path in template_files.items():
        template_path = os.path.join('templates', template_file)
        if not os.path.exists(template_path):
            if os.path.exists(default_path):
                import shutil
                shutil.copy(default_path, template_path)
                logging.info(f"Created {template_file} from defaults")
            else:
                # Fallback templates
                fallback_templates = {
                    'active_message.txt': 'Dear {Client}, your hearing for {Parties} is on {NextHearingDate}. Please be prepared. Best regards, Legal Team.',
                    'inactive_message.txt': 'Dear {Client}, please contact us regarding your case {Parties}. Best regards, Legal Team.',
                    'no_instruction_message.txt': 'Dear {Client}, we need your instructions for {Parties} before {NextHearingDate}. Please contact us urgently. Best regards, Legal Team.'
                }
                with open(template_path, 'w') as f:
                    f.write(fallback_templates.get(template_file, ''))
                logging.info(f"Created fallback {template_file}")

create_upload_dirs()
initialize_default_configs()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config')
def config():
    # Load existing configuration and templates
    config_data = {}
    templates_data = {}
    
    # Load config.json
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            config_data = json.load(f)
    
    # Load template files
    template_files = ['active_message.txt', 'inactive_message.txt', 'no_instruction_message.txt']
    for template_file in template_files:
        template_path = os.path.join('templates', template_file)
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                templates_data[template_file.replace('.txt', '')] = f.read()
    
    return render_template('config.html', config=config_data, templates=templates_data)

@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'csv_file' not in request.files:
        return jsonify({'error': 'No file selected'}), 400
    
    file = request.files['csv_file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Validate CSV structure
        try:
            df = pd.read_csv(file_path)
            required_columns = ['Client', 'Contact', 'NextHearingDate', 'Category', 'TypRnRy', 'Parties']
            if not all(col in df.columns for col in required_columns):
                return jsonify({'error': f'CSV must contain columns: {", ".join(required_columns)}'}), 400
            
            session['csv_path'] = file_path
            return jsonify({'success': 'CSV uploaded successfully', 'rows': len(df)})
        except Exception as e:
            return jsonify({'error': f'Error reading CSV: {str(e)}'}), 400
    
    return jsonify({'error': 'Invalid file format'}), 400

@app.route('/save_templates', methods=['POST'])
def save_templates():
    data = request.json
    
    try:
        # Save message templates
        templates = {
            'active_message.txt': data.get('active_template', ''),
            'inactive_message.txt': data.get('inactive_template', ''),
            'no_instruction_message.txt': data.get('no_instruction_template', '')
        }
        
        for filename, content in templates.items():
            with open(os.path.join('templates', filename), 'w') as f:
                f.write(content)
        
        # Save configuration
        config_data = {
            'notification_contact1': data.get('notification_contact1', ''),
            'notification_contact2': data.get('notification_contact2', ''),
            'user_data_type': data.get('user_data_type', 'shs')
        }
        
        with open('config.json', 'w') as f:
            json.dump(config_data, f, indent=2)
        
        return jsonify({'success': 'Configuration saved successfully'})
    except Exception as e:
        return jsonify({'error': f'Error saving configuration: {str(e)}'}), 400

@app.route('/start_messaging', methods=['POST'])
def start_messaging():
    global message_status
    
    if message_status['is_running']:
        return jsonify({'error': 'Messaging is already in progress'}), 400
    
    # Check if we have uploaded files
    upload_files = [f for f in os.listdir('uploads') if f.endswith('.csv')]
    if not upload_files:
        return jsonify({'error': 'Please upload a CSV file first'}), 400
    
    # Use the most recent CSV file
    csv_path = os.path.join('uploads', max(upload_files, key=lambda f: os.path.getctime(os.path.join('uploads', f))))
    
    # Start messaging in a separate thread
    thread = threading.Thread(target=run_messaging_process, args=(csv_path,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': 'Messaging process started'})

@app.route('/status')
def get_status():
    return jsonify(message_status)

@app.route('/logs')
def logs():
    return render_template('logs.html')

def run_messaging_process(csv_path):
    global message_status
    
    message_status['is_running'] = True
    message_status['current_step'] = 'Initializing...'
    message_status['progress'] = 0
    message_status['messages'] = []
    
    try:
        # Load configuration
        config_path = 'config.json'
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {
                'notification_contact1': '',
                'notification_contact2': '',
                'user_data_type': 'shs'
            }
        
        # Process CSV
        message_status['current_step'] = 'Processing CSV file...'
        df = pd.read_csv(csv_path, dtype={"Contact": str})
        df['Contact'] = df['Contact'].str.replace(" ", "").str.strip()
        
        # Filter clients
        message_status['current_step'] = 'Filtering clients...'
        today = datetime.now().date() + timedelta(days=6)
        selected_categories = ["Active", "NoClientsInstruction"]
        
        clients = df[['Client', 'Contact', 'NextHearingDate', 'Category', 'TypRnRy', 'Parties']]
        clients.loc[:, 'NextHearingDate'] = pd.to_datetime(clients['NextHearingDate'], errors='coerce').dt.date
        
        filtered_clients = clients[clients['Category'].isin(selected_categories)]
        today_clients = filtered_clients[filtered_clients['NextHearingDate'] == today]
        
        message_status['total'] = len(today_clients)
        
        # Load message templates
        templates = {}
        template_files = {
            'Active': 'templates/active_message.txt',
            'NoClientsInstruction': 'templates/no_instruction_message.txt'
        }
        
        for category, file_path in template_files.items():
            with open(file_path, 'r') as f:
                templates[category] = f.read()
        
        # Initialize WebDriver
        message_status['current_step'] = 'Initializing browser...'
        driver = initialize_webdriver_for_webapp()
        
        if not check_session_webapp(driver):
            message_status['current_step'] = 'Session check failed'
            message_status['is_running'] = False
            return
        
        # Send messages
        message_status['current_step'] = 'Sending messages...'
        
        for index, (_, row) in enumerate(today_clients.iterrows()):
            name = row['Client']
            contact = row['Contact']
            category = row['Category']
            
            # Get message template
            message_template = templates.get(category, '')
            message = message_template
            
            # Replace placeholders
            for col in clients.columns:
                if col in row:
                    message = message.replace(f"{{{col}}}", str(row[col]))
            
            # Send message
            success = send_whatsapp_message_webapp(driver, name, contact, message)
            
            message_status['progress'] = index + 1
            message_status['messages'].append({
                'client': name,
                'contact': contact,
                'status': 'Success' if success else 'Failed'
            })
            
            time.sleep(5)  # Delay between messages
        
        driver.quit()
        message_status['current_step'] = 'Completed'
        message_status['is_running'] = False
        
    except Exception as e:
        message_status['current_step'] = f'Error: {str(e)}'
        message_status['is_running'] = False

def initialize_webdriver_for_webapp():
    """Initialize WebDriver for web app"""
    options = Options()
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Create user data directory for session persistence
    user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
    os.makedirs(user_data_dir, exist_ok=True)
    options.add_argument(f"--user-data-dir={user_data_dir}")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(20)
        driver.get("https://web.whatsapp.com")
        logging.info("WebDriver initialized successfully")
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize WebDriver: {e}")
        raise

def check_session_webapp(driver):
    """Check if WhatsApp Web session is active"""
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "pane-side"))
        )
        return True
    except Exception:
        return False

def send_whatsapp_message_webapp(driver, name, contact, message):
    """Send WhatsApp message for web app"""
    try:
        encoded_message = urllib.parse.quote(message)
        url = f"https://web.whatsapp.com/send?phone={contact}&text={encoded_message}"
        driver.get(url)
        
        send_button_xpaths = [
            '//*[@id="main"]/footer/div[1]/div/span/div/div[2]/div/div[4]/button',
            '//span[@data-testid="send"]'
        ]
        
        for xpath in send_button_xpaths:
            try:
                send_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                time.sleep(2)
                send_button.click()
                return True
            except Exception:
                continue
        
        return False
    except Exception:
        return False

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
