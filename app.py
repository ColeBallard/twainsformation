from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
import os
import requests

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
    # Extract data from form
    user_input = request.form.get('textInput')  # Changed from 'user_input' to 'textInput'

    # Optional: Handling file upload
    # if 'file' in request.files:
    #     file = request.files['file']
    #     # Process file here

    # Call OpenAI API
    try:
        response = call_openai_gpt4(user_input)
    except Exception as e:
        return jsonify({"error": str(e)})

    response_data = response['choices'][0]['message']['content']  # Extracting specific data from the response

    return response_data

def call_openai_gpt4(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": "Bearer " + api_key,  # Added space after 'Bearer'
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        return response.json()
    except requests.RequestException as e:
        raise SystemExit(e)


if __name__ == '__main__':
    app.run(debug=True)
