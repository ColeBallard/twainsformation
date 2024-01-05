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

        segmented_text = read_file(save_path)

        total_length = len(segmented_text)

        transformed_book = [transform_text(request.form, segment, index, total_length) for index, segment in enumerate(segmented_text)]

        # Save or process the transformed book
        with open('transformed_book.txt', 'w') as file:
            file.write(" ".join(transformed_book))

        return jsonify({"message": "File uploaded successfully"}), 200

def transform_text(form, segment, index, total_length):
    prompt = form.get('prompt')  # Changed from 'user_input' to 'textInput'
    chatgpt_model = form.get('chatgptModel')

    prompt = f"Transform this text to {prompt} style: {segment}"

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
        print(f'{index + 1}/{total_length}')
        return response.json()['choices'][0]['message']['content']
    except requests.RequestException as e:
        raise SystemExit(e)

def read_file(file_path):
    encoding = tiktoken.get_encoding("cl100k_base")
    encoding = tiktoken.encoding_for_model("gpt-4")

    combined_content = ""  # Initialize an empty string to accumulate the lines
    with open(file_path, 'r') as file:
        for line in file:
            combined_content += line.strip()  # Append each line to the combined_content string
    # print(combined_content)  # Print the combined content after reading all lines
    # print(num_tokens_from_string(combined_content, "cl100k_base"))

    segmented_text = segment_text(combined_content, 4096)

    print(len(segmented_text))
    print(num_tokens_from_string(segmented_text[0], "cl100k_base"))

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

if __name__ == '__main__':
    app.run(debug=True)
