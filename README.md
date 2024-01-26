# Twainsformation

## Description

Toolkit powered by ChatGPT for creating, modifying the style of, and condensing a piece of literature.

## Features

- Change the style of a long-form piece of literature
  - Style change is applied to the entire piece

## Future Features

- Create a long-form piece of literature based on comprehensive details
  - Use an outline
  - Use beginning, middle, and end
  - Use a plot
- Condense a piece of literature
  - Condense into a few paragraphs
  - Condense into a few pages
  - Condense into 10-50 pages
- Export to pdf

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
pip install -r requirements.txt
```

4. [Create an OpenAI account and get an API Key.](https://www.maisieai.com/help/how-to-get-an-openai-api-key-for-chatgpt)

5. Run app.py.

```shell
python app.py
```

6. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

7. Download a publicly-available book in text-file format. Some good places to look are [Project Gutenberg](https://www.gutenberg.org/) and [Internet Archive](https://archive.org/).

8. Write your OpenAI API Key in the designated input field, upload a text file, choose a prompt, and wait for ChatGPT to transform the piece of literature.

9. Feel free to leave feedback about the quality of the produced text [via email](https://coleb.io/contact).

## **[Contact](https://coleb.io/contact)**
