import webbrowser
import threading
import tkinter as tk
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import datetime
import requests
import tiktoken

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
import base64

app = Flask(__name__, static_folder='.', static_url_path='')

# Load the environment variables from .env file
load_dotenv()

# Access the API key
api_key = os.getenv('OPENAI_API_KEY')

@app.route('/', methods=['GET', 'POST'])
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/submit-form', methods=['POST'])
def submit_form():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    UPLOAD_FOLDER = '/path/to/save'

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        print('File uploaded successfully')

        segmented_text = read_file(save_path)

        total_length = len(segmented_text)

        form = request.form
        title = form.get('title')
        author = form.get('author')
        prompt = form.get('prompt')
        chatgpt_model = form.get('chatgptModel')

        transformed_book = [transform_text(title, author, prompt, chatgpt_model, segment, index, total_length) for index, segment in enumerate(segmented_text)]

        # Save or process the transformed book
        with open(f'{title} {datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.txt', 'w') as file:
            file.write(' '.join(transformed_book))

        return jsonify({'message': 'File uploaded successfully'}), 200

def transform_text(title, author, prompt, chatgpt_model, segment, index, total_length):
    instruction = f'Here is a section of {title} by {author}. {prompt}: {segment}'

    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': 'Bearer ' + api_key,  # Added space after 'Bearer'
        'Content-Type': 'application/json'
    }
    data = {
        'model': chatgpt_model,
        'messages': [{'role': 'user', 'content': instruction}],
        'temperature': 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        print(f'{index + 1}/{total_length}')
        return response.json()['choices'][0]['message']['content']
    except requests.RequestException as e:
        raise SystemExit(e)

def read_file(file_path):
    encoding = tiktoken.get_encoding('cl100k_base')
    encoding = tiktoken.encoding_for_model('gpt-4')

    combined_content = ''  # Initialize an empty string to accumulate the lines
    with open(file_path, 'r') as file:
        for line in file:
            combined_content += line.strip()  # Append each line to the combined_content string
    # print(combined_content)  # Print the combined content after reading all lines
    # print(num_tokens_from_string(combined_content, 'cl100k_base'))

    segmented_text = segment_text(combined_content, 4096)

    print(len(segmented_text))
    print(num_tokens_from_string(segmented_text[0], 'cl100k_base'))

    return segmented_text

def segment_text(text, max_length):
    segments = []
    start_index = 0

    while start_index < len(text):
        # Determine the end index for this segment
        end_index = min(start_index + max_length, len(text))
        
        # Find the position of the last period before or at the end index
        period_index = text.rfind('.', start_index, end_index)

        # If no period is found, extend to the next period
        if period_index == -1 or period_index < start_index:
            period_index = text.find('.', end_index)
            if period_index == -1:  # If there's no more periods in the text
                period_index = len(text) - 1

        # Extract the segment and add to the list
        segment = text[start_index:period_index + 1].strip()
        segments.append(segment)

        # Update the start index for the next segment
        start_index = period_index + 1

    return segments

def num_tokens_from_string(string, encoding_name):
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

# Function to generate a key from a passphrase
def generate_key_from_passphrase(passphrase):
    salt = b'\x1a\xa9\x9e\x9f\x1f\x9f\x9b\xab\x1d\xde\xdf\xef\xff\xfe\xfd\xfc'  # Use a fixed salt
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
    return key

# Encrypting the code
def encrypt_code(code, passphrase):
    key = generate_key_from_passphrase(passphrase)
    cipher_suite = Fernet(key)
    encrypted_code = cipher_suite.encrypt(code.encode())
    return encrypted_code

# Decrypting the code
def decrypt_code(encrypted_code, passphrase):
    key = generate_key_from_passphrase(passphrase)
    cipher_suite = Fernet(key)
    decrypted_code = cipher_suite.decrypt(encrypted_code).decode()
    return decrypted_code

# Function to open the web page in a browser
def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000/')

def run_gui():
    root = tk.Tk()
    root.title("Status Window")
    
    # Example label
    label = tk.Label(root, text="Status Messages Here")
    label.pack()

    # Function to handle API Key management
    def manage_api_keys():
        api_key_window = tk.Toplevel(root)
        api_key_window.title("API Key Management")
        
        # Example label in API Key window
        label = tk.Label(api_key_window, text="Enter and store your API Keys here")
        label.pack()

        # Example of API Key input
        api_key_input = tk.Entry(api_key_window)
        api_key_input.pack()

        # Save button (Implement saving logic as needed)
        save_button = tk.Button(api_key_window, text="Save", command=lambda: save_api_key(api_key_input.get()))
        save_button.pack()

    # Example function to save API Key (Implement actual saving logic)
    def save_api_key(api_key):
        print("API Key saved:", api_key)  # Replace with actual save logic

    # Creating a menu bar
    menubar = tk.Menu(root)

    # Creating a 'File' menu
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="API Keys", command=manage_api_keys)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=file_menu)

    # Adding the menu bar to the window
    root.config(menu=menubar)

    # Run the Tkinter event loop
    root.mainloop()

# Running Flask in a separate thread
def run_flask():
    app.run()

if __name__ == '__main__':
    # Start Flask in a new thread
    threading.Thread(target=run_flask, daemon=True).start()

    # Open the browser
    open_browser()

    # Run the GUI
    run_gui()
