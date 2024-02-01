from flask import Flask, request, jsonify, send_from_directory, url_for, send_file
from werkzeug.utils import secure_filename
from fpdf import FPDF
import os
import re
import datetime
import requests
import tiktoken
import threading

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

progress_data = {}

# ROUTES

@app.route('/', methods=['GET', 'POST'])
def index():
    return send_from_directory('.', 'index.html')

@app.route('/style-changer', methods=['POST'])
def submit_style_changer_form():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    UPLOAD_FOLDER = '/tmp/uploaded_books'

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

    # Start the processing in a separate thread
    threading.Thread(target=process_file, args=(filename, title, author, prompt, chatgpt_model, api_key, total_length)).start()

    # transformed_book = [transform_text(title, author, prompt, chatgpt_model, api_key, segment, index, total_length) for index, segment in enumerate(segmented_text)]

    # Save or process the transformed book
    # with open(f'{title} {datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.txt', 'w') as file:
    #     file.write(' '.join(transformed_book))

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

    outline_descriptions = [write_text(title, endpoint, chatgpt_model, api_key, total_length, 'outline') for endpoint in endpoints]

    outline_descriptions_list = '\n'.join(outline_descriptions)

    split_list = outline_descriptions_list.split('\n')

    filtered_paragraphs = [p for p in split_list if re.match(r'^\d+\.', p)]

    print(filtered_paragraphs)

    final_text = [write_text(title, filtered_paragraph, chatgpt_model, api_key, total_length, 'outline description') for filtered_paragraph in filtered_paragraphs]

    # Save or process the transformed book
    with open(f'{title} {datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.txt', 'w') as file:
        file.write(' '.join(final_text))

    return jsonify({'message': 'File uploaded successfully'}), 200

@app.route('/progress')
def progress():
    return jsonify(progress_data)

# Flask route to create and serve PDF
@app.route('/create-pdf', methods=['POST'])
def pdf_route():
    data = request.json
    print(data)
    pdf_full_path = create_pdf(data['text'], data['title'])

    # Send the PDF file directly to the client for download
    return send_file(pdf_full_path, as_attachment=True)

def create_pdf(text, title):
    pdf = FPDF()
    pdf.set_margins(20, 20, 20)  # Set larger margins (20mm on each side)
    pdf.add_page()

    # Set font for the title to Times New Roman, bold, size 24
    pdf.set_font("Times", 'B', 24)
    pdf_w = 210 - 40  # Adjust width for the new margins
    title_w = pdf.get_string_width(title) + 6
    title_x = (pdf_w - title_w) / 2 + 20  # Adjust for left margin
    title_y = (297 - 10) / 4  # Place title roughly in the upper third
    
    pdf.set_xy(title_x, title_y)
    pdf.cell(title_w, 10, title, 0, 1, 'C')
    
    pdf.add_page()
    pdf.set_font("Times", size=12)
    
    # Process each paragraph for indentation and reduced line spacing
    indent = 10  # Indentation for paragraphs in mm
    line_height = 8  # Adjust line height for tighter spacing
    paragraphs = text.split('\n')
    
    for paragraph in paragraphs:
        if paragraph.strip():  # Check if paragraph is not just whitespace
            pdf.set_x(pdf.l_margin + indent)  # Apply indentation
            pdf.multi_cell(0, line_height, paragraph)
        else:
            pdf.ln(6)  # Add a blank line for paragraph spacing

    # Define a temporary directory within /tmp for PDFs
    pdf_directory = '/tmp/transformed_books'  # Adjusted to /tmp for compatibility
    
    # Check if the directory exists, and create it if it doesn't
    if not os.path.exists(pdf_directory):
        os.makedirs(pdf_directory)

    # Secure the title and replace spaces with underscores
    safe_title = secure_filename(title).replace(' ', '_')

    # Generate a timestamp string
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    # Append the timestamp to the safe_title
    safe_title = f"{safe_title}{timestamp}.pdf"

    pdf_full_path = os.path.join(pdf_directory, safe_title)

    # Save the PDF file
    pdf.output(pdf_full_path)

    # Return the relative path from the static folder
    # relative_path = os.path.join('transformed_books', f"{safe_title}.pdf").replace('\\', '/')
    return pdf_full_path

def process_file(filename, title, author, prompt, chatgpt_model, api_key, total_length):
    # Assuming read_file and transform_text are defined elsewhere
    segmented_text = read_file(os.path.join('/uploaded_books', filename))
    
    transformed_book = []
    for index, segment in enumerate(segmented_text):
        transformed_segment = transform_text(title, author, prompt, chatgpt_model, api_key, segment, index, total_length)
        transformed_book.append(transformed_segment)
        
        # Update progress
        progress_data['current'] = index + 1
        progress_data['total'] = total_length
        progress_data['text'] = ' '.join(transformed_book)
    
    # # Save the transformed book
    # with open(os.path.join('/transformed_books', f'{title}_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.txt'), 'w') as file:
    #     file.write(' '.join(transformed_book))

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

def write_text(title, prompt, chatgpt_model, api_key, total_length, outline_or_description):
    if outline_or_description == 'outline':
        instruction = f'Here is a part of an outline from the book {title}. {prompt}. Can you expand upon this via a numbered list, filling in the gaps where necessary?'
    elif outline_or_description == 'outline description':
        instruction = f'Here is a description of an outline from the book {title}. {prompt}. Can you elaborate on this descrption, filling in the gaps where necessary?'

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
    combined_content = ''  # Initialize an empty string to accumulate the lines
    with open(file_path, 'r') as file:
        for line in file:
            combined_content += line.strip()  # Append each line to the combined_content string

    segmented_text = segment_text(combined_content, 4096)

    print(f'Total characters: {len(segmented_text)}')
    print(f'Total tokens: {num_tokens_from_string(segmented_text[0], 'cl100k_base')}')

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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
