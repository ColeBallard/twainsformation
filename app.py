from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import requests
import tiktoken

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
    encoding = tiktoken.get_encoding("cl100k_base")
    encoding = tiktoken.encoding_for_model(request.form.get('chatgptModel'))

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    UPLOAD_FOLDER = '/path/to/save'

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        print("File uploaded successfully")

        read_file(save_path)

        return jsonify({"message": "File uploaded successfully"}), 200

    # Optional: Handling file upload
    # if 'file' in request.files:
    #     file = request.files['file']
    #     # Process file here

    # # Call OpenAI API
    # try:
    #     response = call_openai_gpt4(request.form)
    # except Exception as e:
    #     return jsonify({"error": str(e)})

    # response_data = response['choices'][0]['message']['content']  # Extracting specific data from the response

    # return response_data

def call_openai_gpt4(form):
    prompt = form.get('prompt')  # Changed from 'user_input' to 'textInput'
    chatgpt_model = form.get('chatgptModel')

    print(chatgpt_model)

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": "Bearer " + api_key,  # Added space after 'Bearer'
        "Content-Type": "application/json"
    }
    data = {
        "model": chatgpt_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        return response.json()
    except requests.RequestException as e:
        raise SystemExit(e)

def read_file(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            # Process each line
            print(line.strip())  # .strip() removes leading/trailing whitespace, including newline characters

if __name__ == '__main__':
    app.run(debug=True)
