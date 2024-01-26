import webbrowser
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import re
import datetime
import requests
import tiktoken

app = Flask(__name__, static_folder='.', static_url_path='')

class OutlineNode:
    def __init__(self, value, level):
        self.value = value
        self.level = level
        self.children = []

    def add_child(self, node):
        self.children.append(node)

    def is_endpoint(self):
        return len(self.children) == 0

@app.route('/', methods=['GET', 'POST'])
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

@app.route('/style-changer', methods=['POST'])
def submit_style_changer_form():
    form_type = request.form.get('form_id')

    print(form_type)

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    UPLOAD_FOLDER = '/uploaded_books'

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not file:
        return 'No file selected'
    
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
    api_key = form.get('api_key')

    transformed_book = [transform_text(title, author, prompt, chatgpt_model, api_key, segment, index, total_length) for index, segment in enumerate(segmented_text)]

    # Save or process the transformed book
    with open(f'{title} {datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.txt', 'w') as file:
        file.write(' '.join(transformed_book))

    return jsonify({'message': 'File uploaded successfully'}), 200
    
@app.route('/book-writer', methods=['POST'])
def submit_book_writer_form():
    print(request.json)

    data = request.json['outline']
    title = request.json['title']
    api_key = request.json['api_key']

    tree = parse_to_tree(data)
    endpoints = concatenate_endpoints(tree)

    total_length = len(endpoints)

    chatgpt_model = 'gpt-3.5-turbo'

    endpoints = ['They are attacked by the dark sorcerer, Malcor, who has been following them']

    result_list = [write_text(title, endpoint, chatgpt_model, api_key, total_length) for endpoint in endpoints]

    final_text = '\n'.join(result_list)

    split_list = final_text.split('\n')

    filtered_paragraphs = [p for p in split_list if re.match(r'^\d+\.', p)]

    print(filtered_paragraphs)

    # Save or process the transformed book
    with open(f'{title} {datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.txt', 'w') as file:
        file.write(' '.join(endpoints))

    return jsonify({'message': 'File uploaded successfully'}), 200

def transform_text(title, author, prompt, chatgpt_model, api_key, segment, index, total_length):
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

def write_text(title, prompt, chatgpt_model, api_key, total_length):
    instruction = f'Here is a part of an outline from the book {title}. {prompt}. Can you expand upon this via a numbered list, filling in the gaps where necessary?'

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
        print(f'{1}/{total_length}')
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


def parse_to_tree(data):
    root = OutlineNode("", "0")  # Root node
    last_nodes = {0: root}

    for item in data:
        current_level = len(item['level'].split('.'))
        node = OutlineNode(item['value'], item['level'])
        last_nodes[current_level - 1].add_child(node)
        last_nodes[current_level] = node

    return root

def concatenate_endpoints(node, path_string=""):
    if node.level != "0":  # Skip the root node
        path_string += (node.value + "\n")
    
    if node.is_endpoint():
        return [path_string.strip()]  # Return the concatenated string for this endpoint

    concatenated = []
    for child in node.children:
        concatenated.extend(concatenate_endpoints(child, path_string))

    return concatenated

if __name__ == '__main__':
    webbrowser.open_new('http://127.0.0.1:5000/')
    app.run()
