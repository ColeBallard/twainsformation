# Twainsformation

## Description

Web application powered by ChatGPT for creating, modifying the style of, and condensing a piece of literature.

## Features

- Change the style of a long-form piece of literature
  - Style change is applied to the entire piece
- Create a long-form piece of literature based on comprehensive details
  - Use an outline
  - Use a summary
- Export to pdf

## Future Features

- Create a long-form piece of literature based on comprehensive details
  - Use nothing! Let ChatGPT handle all the ideas
  - Use your likes and dislikes to create a novel fit for you
- Condense a piece of literature
  - Condense into a few paragraphs
  - Condense into a few pages
  - Condense into 10-50 pages

## Note

- The application **never** stores or uses your API Key outside of your own prompts. All of the code in this repository is public.
- The application uses gpt-3.5-turbo for the vast majority of prompts and each tick mark on the loading bar is about .2 cents. Most prompts total out between 2 - 15 cents.

## Design

- user provides .txt file of a writing (e.g., book or short story) and a prompt to be applied to the entire text
- a pdf file is created with the ChatGPT changes

## Requirements

Must have an Open-AI API Key.

## Usage

1. [Create an OpenAI account and get an API Key.](https://www.maisieai.com/help/how-to-get-an-openai-api-key-for-chatgpt)

2. Go to [https://twainsformation-a15e0b6a5751.herokuapp.com/](https://twainsformation-a15e0b6a5751.herokuapp.com/).

3. Press the API Key button, then paste your OpenAI API Key in the designated input field.

4. Click on either the Style Changer or Book Writer tab.

5. Fill out the forms and press the Submit button whenever your prompt is ready.

6. The application will use iteration and strategic prompting to create a book.

7. A pdf will automatically be downloaded whenever the loading bar gets to 100%.

8. Feel free to leave feedback about the quality of the produced text [via email](https://coleb.io/contact).

## Contribution

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

8. Press the API Key button, then paste your OpenAI API Key in the designated input field.

9. Feel free to leave feedback about the quality of the produced text [via email](https://coleb.io/contact).

## **[Contact](https://coleb.io/contact)**
