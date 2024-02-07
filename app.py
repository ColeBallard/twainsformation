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

    return jsonify({'message': 'File uploaded successfully'}), 200
    
@app.route('/book-writer', methods=['POST'])
def submit_book_writer_form():
    print(request.json)

    data = request.json['outline']
    title = request.json['title']
    api_key = request.json['api_key']

    tree = parse_to_tree(data)
    endpoints = concatenate_endpoints(tree)

    chatgpt_model = 'gpt-3.5-turbo'

    # Start the processing in a separate thread
    threading.Thread(target=process_outline, args=(title, endpoints, chatgpt_model, api_key)).start()

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

    text = sanitize_text(text)

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
    safe_title = f"{safe_title}_{timestamp}.pdf"

    pdf_full_path = os.path.join(pdf_directory, safe_title)

    # Save the PDF file
    pdf.output(pdf_full_path)

    return pdf_full_path

def sanitize_text(text):
    # Replace specific non-Latin-1 characters with their Latin-1 equivalents or remove them
    return text.replace('\u2013', '-').replace('\u2014', '--').replace('\u2018', "'").replace('\u2019', "'").replace('\u2026', '...')  # Add more replacements as needed

def process_file(filename, title, author, prompt, chatgpt_model, api_key, total_length):
    # Assuming read_file and transform_text are defined elsewhere
    segmented_text = read_file(os.path.join('/tmp/uploaded_books', filename))
    
    transformed_book = []
    for index, segment in enumerate(segmented_text):
        transformed_segment = transform_text(title, author, prompt, chatgpt_model, api_key, segment, index, total_length)
        transformed_book.append(transformed_segment)
        
        # Update progress
        progress_data['current'] = index + 1
        progress_data['total'] = total_length
        progress_data['text'] = ' '.join(transformed_book)

def process_outline(title, paragraphs, chatgpt_model, api_key):
    total_length = len(paragraphs)
    estimated_total_length = total_length * 20
    progress_data['total'] = estimated_total_length

    progress_data['current'] = 0

    outlines = []
    for index, paragraph in enumerate(paragraphs):
        outline = write_text(title, paragraph, chatgpt_model, api_key, estimated_total_length, 'outline')
        outlines.append(outline)
        
        # Update progress
        progress_data['current'] = progress_data['total']  - 1 if progress_data['current'] + 1 == progress_data['total']  else progress_data['current'] + 1

    outline_descriptions = '\n'.join(outlines)
    outline_descriptions = outline_descriptions.split('\n')
    outline_descriptions = [p for p in outline_descriptions if re.match(r'^\d+\.', p)]

    total_length += len(outline_descriptions)
    estimated_total_length = len(paragraphs) + (len(outline_descriptions) * 2)
    progress_data['total'] = estimated_total_length

    expanded_outlines = []
    for index, paragraph in enumerate(outline_descriptions):
        outline_description = write_text(title, paragraph, chatgpt_model, api_key, estimated_total_length, 'outline description')
        expanded_outlines.append(outline_description)
        
        # Update progress
        progress_data['current'] = progress_data['total']  - 1 if progress_data['current'] + 1 == progress_data['total']  else progress_data['current'] + 1

    expanded_outlines = segment_text(''.join(expanded_outlines), 4096)

    total_length += len(expanded_outlines)
    progress_data['total'] = total_length

    final_text = []
    for index, paragraph in enumerate(expanded_outlines):
        final_segment = write_text(title, paragraph, chatgpt_model, api_key, estimated_total_length, 'expanded outline')
        final_text.append(final_segment)
        
        # Update progress
        progress_data['current'] = progress_data['current'] + 1

    # Store final text in progress
    progress_data['text'] = ''.join(final_text)

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
    reality = 'fiction'

    if reality == 'fiction':
        if outline_or_description == 'outline':
            instruction = f"Below is a segment from the outline of my story titled '{title}'. Based on this segment: {prompt}. Could you expand upon this by creating a numbered list (1-10) that outlines a series of events for this part of the story? Please ensure each event is detailed and contributes to the development of the plot or characters. Also, consider the logical progression of events and how they connect to the overall narrative. This list should help in further fleshing out the story's structure and guide the subsequent drafting process."
        elif outline_or_description == 'outline description':
            instruction = f"Here is a section from the outline of my story titled {title}. Based on this outline: {prompt}. Please write this part of the story in a detailed narrative prose format, focusing on descriptive storytelling. Include descriptions of settings, characters' thoughts and dialogue, and actions, and ensure the story flows smoothly from one scene to the next. Avoid presenting the story as a script or an outline. Fill in the gaps as necessary to create a cohesive and engaging narrative."
        elif outline_or_description == 'expanded outline':
            instruction = f"Below is a segment from the rough draft of my story titled '{title}'. {prompt}. Could you revise this to make the narrative more cohesive? Focus on improving the flow of events, enhancing character development, and ensuring that the transitions between scenes are smooth. Additionally, please look for any inconsistencies in the plot or character actions and address them. My goal is to have a seamless narrative that clearly conveys the story's progression and deepens the reader's engagement with the characters and their journey."
    elif reality == 'non-fiction':
        if outline_or_description == 'outline':
            instruction = f'Here is a part of an outline from the book {title}. {prompt}. Can you expand upon this by making a numbered list (1-10), filling in the gaps where necessary?'
        elif outline_or_description == 'outline description':
            instruction = f'Here is a description of an outline from the book {title}. {prompt}. Can you elaborate on this description, filling in the gaps where necessary?'

    print(instruction)

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
