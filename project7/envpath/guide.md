## Virtual Environment for your localhost :D

> Create and activate a python virtual environment:

mkdir project7

cd project7

python3.9 -m venv envpath

source envpath/bin/activate

> Install the required packages:

pip install -r requirements.txt

> Create .env file for API keys:

touch .env

- GROQ_API_KEY=
- TAVILY_API_KEY=

> Create a folder for saved reports:

mkdir saved_pages

> Run flask

python app.py

>Important notes:
>>1. Make sure you have Python 3.7+ installed on your machine
>>
>>2. You'll need to get your own API keys from:
>>
>>- Groq: https://console.groq.com/
>>
>>- Tavily: https://tavily.com/
>>
>>3. The saved_pages directory is where the application will store saved research outputs
