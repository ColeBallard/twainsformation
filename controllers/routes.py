import os
import re
import threading
import requests

from flask import request, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename

from features.style_changer import StyleChanger
from models.story_pdf import StoryPDF
from utilities.outline_node import OutlineNode
import prompt_templates as pt

def configure_routes(app):

    @app.route('/', methods=['GET', 'POST'])
    def index():
        return send_from_directory('.', 'index.html')

    @app.route('/style-changer', methods=['POST'])
    def run_style_changer():
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file part'}), 400
            
            file = request.files['file']

            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            
        except Exception as e:
            return jsonify({'error': 'Error selecting file'}), 400
        
        try:
            UPLOAD_FOLDER = '/tmp/uploaded_books'

            if not os.path.exists(UPLOAD_FOLDER):
                os.makedirs(UPLOAD_FOLDER)
            
            filename = secure_filename(file.filename)
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(save_path)

            print('File uploaded successfully')

        except Exception as e:
            return jsonify({'error': 'Error saving file'}), 400

        try:
            styler_changer = StyleChanger(request.form, filename, save_path)
            styler_changer.start()
        except Exception as e:
            return jsonify({'message': f'Error changing style of {filename}'}), 400

        return jsonify({'message': 'File uploaded successfully'}), 200
        
    @app.route('/book-writer', methods=['POST'])
    def submit_book_writer_form():
        progress_data['complete'] = False

        data = request.json
        title = data['title']
        api_key = data['api_key']
        chatgpt_model = 'gpt-4o-mini'

        if 'outline' in data:
            outline_data = data['outline']
            tree = parse_to_tree(outline_data)
            endpoints = concatenate_endpoints(outline_data)
            threading.Thread(target=process_outline, args=(title, outline_data, chatgpt_model, api_key)).start()
        elif 'summary' in data:
            summary_data = data['summary']
            threading.Thread(target=process_summary, args=(title, summary_data, chatgpt_model, api_key)).start()

        return jsonify({'message': 'Processing started successfully'}), 200

    @app.route('/progress')
    def progress():
        return jsonify(progress_data)

    # Flask route to create and serve PDF
    @app.route('/create-pdf', methods=['POST'])
    def pdf_route():
        data = request.json
        print(data)

        story_pdf = StoryPDF(data['text'], data['title'])
        pdf_full_path = story_pdf.create()

        # Send the PDF file directly to the client for download
        return send_file(pdf_full_path, as_attachment=True)
    
progress_data = {}

# ROUTES

def process_outline(title, paragraphs, chatgpt_model, api_key):
    total_length = len(paragraphs)
    estimated_total_length = total_length * 20
    progress_data['total'] = estimated_total_length
    
    progress_data['current'] = 0

    outlines = []
    for index, paragraph in enumerate(paragraphs):
        outline = write_text(title, [paragraph], chatgpt_model, api_key, estimated_total_length, 'outline')
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
        outline_description = write_text(title, [paragraph], chatgpt_model, api_key, estimated_total_length, 'outline description')
        expanded_outlines.append(outline_description)
        
        # Update progress
        progress_data['current'] = progress_data['total']  - 1 if progress_data['current'] + 1 == progress_data['total']  else progress_data['current'] + 1

    expanded_outlines = segment_text(''.join(expanded_outlines), 4096)

    total_length += len(expanded_outlines)
    progress_data['total'] = total_length

    final_text = []
    for index, paragraph in enumerate(expanded_outlines):
        final_segment = write_text(title, [paragraph], chatgpt_model, api_key, estimated_total_length, 'expanded outline')
        final_text.append(final_segment)
        
        # Update progress
        progress_data['current'] = progress_data['current'] + 1

    # Store final text in progress
    progress_data['text'] = ''.join(final_text)
    progress_data['complete'] = True

def process_summary(title, summary, chatgpt_model, api_key):
    progress_data['total'] = 51
    progress_data['current'] = 0

    enhanced_summary = write_text(title, [summary], 'gpt-4o', api_key, progress_data['total'], 'summary')
    # Update progress
    progress_data['current'] += 1

    parts_of_summary = write_text(title, [enhanced_summary], 'gpt-4o', api_key, progress_data['total'], 'detailed summary')
    # Update progress
    progress_data['current'] += 1

    # Split the string at each "Chapter X"
    pattern = r'(?=Chapter \d+)'  # Lookahead for 'Chapter ' followed by one or more digits
    parts_of_summary_expanded = re.split(pattern, parts_of_summary)

    # Filter out any empty strings that might result from the split
    parts_of_summary_expanded = [part for part in parts_of_summary_expanded if part.strip()]

    print(parts_of_summary_expanded)

    # Update progress
    progress_data['total'] = progress_data['current'] + (len(parts_of_summary_expanded) * 2) + 1

    parts_list = []
    for index, part in enumerate(parts_of_summary_expanded):
        expanded_part = write_text(title, [enhanced_summary, parts_of_summary, part], chatgpt_model, api_key, progress_data['total'], 'summary parts')
        parts_list.append(expanded_part)
        
        # Update progress
        progress_data['current'] += 1

    # Split the strings and get the new list
    halved_parts_list = split_strings_evenly_by_paragraphs(parts_list)

    # Update progress
    progress_data['total'] = progress_data['current'] + (len(halved_parts_list) / 2) + 1

    cohesive_parts_list = []
    for index, expanded_part in enumerate(halved_parts_list):
        if index == 0:
            cohesive_parts_list.append(expanded_part)
        elif (index % 2) == 1:
            if index == (len(halved_parts_list) - 1):
                cohesive_parts_list.append(expanded_part)
            else:
                cohesive_part = write_text(title, [halved_parts_list[index], halved_parts_list[index + 1]], chatgpt_model, api_key, progress_data['total'], 'expanded parts')
                cohesive_parts_list.append(cohesive_part)
        elif index == (len(halved_parts_list) - 1):
            cohesive_parts_list.append(expanded_part)
        else:
            continue
        
        # Update progress
        progress_data['current'] += 1

    # Store final text in progress
    progress_data['text'] = ''.join(cohesive_parts_list)
    progress_data['complete'] = True

def write_text(title, prompt, chatgpt_model, api_key, total_length, prompt_level):
    instruction = ""

    if prompt_level == 'outline':
        instruction = pt.outline_template_v0010[0].format(title=title, prompt=prompt[0])
    elif prompt_level == 'outline description':
        instruction = pt.outline_template_v0010[1].format(title=title, prompt=prompt[0])
    elif prompt_level == 'expanded outline':
        instruction = pt.outline_template_v0010[2].format(title=title, prompt=prompt[0])
    if prompt_level == 'summary':
        instruction = pt.summary_template_v0002[0].format(title=title, summary=prompt[0])
    elif prompt_level == 'detailed summary':
        instruction = pt.summary_template_v0002[1].format(title=title, summary=prompt[0])
    elif prompt_level == 'summary parts':
        instruction = pt.summary_template_v0002[2].format(title=title, summary=prompt[0], parts=prompt[1], part=prompt[2])
    elif prompt_level == 'expanded parts':
        instruction = pt.summary_template_v0002[3].format(title=title, section1=prompt[0], section2=prompt[1])

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
    
def split_strings_evenly_by_paragraphs(original_strings):
    new_list = []

    for s in original_strings:
        # Split the string into paragraphs
        paragraphs = s.split('\n\n')
        
        # Find the split point
        split_point = len(paragraphs) // 2 + len(paragraphs) % 2  # Ensure first half is equal or larger
        
        # Split the paragraphs into two halves
        first_half = '\n\n'.join(paragraphs[:split_point])
        second_half = '\n\n'.join(paragraphs[split_point:])
        
        # Add the halves to the new list
        new_list.extend([first_half, second_half])

    return new_list

def join_pairs_keep_ends(list_of_strings):
    result_list = [list_of_strings[0]]  # Keep the first element
    
    for i in range(1, len(list_of_strings) - 1, 2):
        joined_string = list_of_strings[i] + " " + list_of_strings[i + 1]  # Join i and i+1 elements
        result_list.append(joined_string)
    
    result_list.append(list_of_strings[-1])  # Keep the last element
    return result_list

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