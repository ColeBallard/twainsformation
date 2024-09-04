import os
import threading
import requests

from utilities.text_utilities import TextUtilities as tu

class StyleChanger():
    def __init__(self, form, filename, save_path): 
        self.filename = filename 
        self.segmented_text = self.readFile(save_path)

        self.total_length = len(self.segmented_text)

        self.title = form.get('title')
        self.author = form.get('author')
        self.prompt = form.get('prompt')
        self.chatgpt_model = form.get('chatgptModel')
        self.api_key = form.get('api_key')

        self.MAX_SEGMENT_CHARS = 4096

    def readFile(self, file_path):
        combined_content = ''  # Initialize an empty string to accumulate the lines
        with open(file_path, 'r') as file:
            for line in file:
                combined_content += line.strip()  # Append each line to the combined_content string

        segmented_text = tu.segmentText(combined_content, self.MAX_SEGMENT_CHARS)

        print(f'Total characters: {len(segmented_text)}')
        print(f'Total tokens: {tu.tokenCount(segmented_text[0])}')

        return segmented_text
    
    def processFile(self, filename, title, author, prompt, chatgpt_model, api_key, total_length, progress_data):
        segmented_text = self.readFile(os.path.join('/tmp/uploaded_books', filename))
        
        transformed_book = []
        for index, segment in enumerate(segmented_text):
            transformed_segment = self.transformText(title, author, prompt, chatgpt_model, api_key, segment, index, total_length)
            transformed_book.append(transformed_segment)
            
            # Update progress
            progress_data['current'] = index + 1
            progress_data['total'] = total_length
            progress_data['text'] = ' '.join(transformed_book)

    def transformText(self, title, author, prompt, chatgpt_model, api_key, segment, index, total_length):
        instruction = f'Here is a section of {title} by {author}. {prompt}: {segment}'

        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Authorization': 'Bearer ' + api_key,
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
        except Exception as e:
            raise Exception('Error requesting ChatGPT')
    
    def start(self, progress_data):
        # Start the processing in a separate thread
        threading.Thread(target=self.processFile, args=(self.filename, self.title, self.author, self.prompt, self.chatgpt_model, self.api_key, self.total_length, progress_data)).start()