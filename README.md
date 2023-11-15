# Twainsformation

## Description

Transform a book or piece of literature into a different style using ChatGPT.

## Design

- user provides .txt file of a writing (e.g., book or short story) and a prompt to be applied to the entire text
- a pdf file is created with the ChatGPT changes

## Requirements

Must have an Open-AI API Key.

## Contribution

If you have an idea or want to report a bug, please create an issue.

## Usage

1. Clone the respository.

```shell
git clone https://github.com/ColeBallard/twainsformation
```

2. Install [the latest version of python.](https://www.python.org/downloads/)

3. Install the dependencies.

```shell
pip install Flask python-dotenv requests
```

4. [Create an OpenAI account and get an API Key.](https://www.maisieai.com/help/how-to-get-an-openai-api-key-for-chatgpt)

5. Fill in the variables in the `.env` file with your information.

```sh
OPENAI_API_KEY = 
```

6. Run app.py.

```shell
python app.py
```

7. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

8. Download a publicly-available book in text-file format. Some good places to look are [Project Gutenberg](https://www.gutenberg.org/) and [Internet Archive](https://archive.org/).

9. Upload the text file, choose a prompt, and wait for ChatGPT to transform the piece of literature.

10. Download the pdf. Feel free to leave feedback about the quality of the produced text [via email](https://coleb.io/contact).

## **[Contact](https://coleb.io/contact)**
