# backend/main.py
import pandas as pd
import sqlite3

from environs import Env
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai

# Initialize the Env instance
env = Env()
env.read_env()  # Reads a .env file if present

# Define and parse environment variables
OPEN_AI_KEY = env.str("OPEN_AI_KEY", default=None)

client = openai.OpenAI(api_key=OPEN_AI_KEY) 
app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load CSV to SQLite
df = pd.read_csv('skaters.csv')
conn = sqlite3.connect('nhl.db', check_same_thread=False)
df.to_sql('players', conn, index=False, if_exists='replace')


def get_table_schema():
    cursor = conn.execute('PRAGMA table_info(players)')
    columns = cursor.fetchall()
    schema = ", ".join([f"{col[1]} ({col[2]})" for col in columns])
    return schema


def question_to_sql(question, schema):
    prompt = f"""
You are an assistant that converts natural language questions into SQL queries.
Return just the sql query please!

The table 'players' has the following columns:
{schema}

In the dataset, the 'situation' column defines game situations. The options for 'situation' are 'all', 'other', '5on5', '4on5', '5on4'.
So when asked about some generic term without directly specifying the situation, search in the 'all' situations: 
for example when asking for a total icetime, search only in situation='all'.
The term 'powerplay' means any row where situation is one of: '5on4', '5on3', or '4on3'.
When asked about powerplay stats, only consider rows with these situations.

IMPORTANT: If the question is about "who scored the most" or "top player(s) or something similar",
return LIMIT 10 players who tie for the highest value (there may be multiple)..
Also, do not show only the names, but also the statistic that was asked!
The column for name is called 'name'


When talking about number of goals scored, use column I_F_Goals for that.

When there is a name specified in lowercase, switch that to correct upper first letter in the word. For example if the question is for 'zach werenski',
use that to 'Zach Werenski'.

The term icetime or total icetime should be calculated as a SUM 
Question: {question}
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert in SQL generation."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()


def summarize_result(result):
    prompt = f"""
The SQL query returned the following results:
{result.to_string(index=False)}

Please summarize these results in a clear, friendly way for a hockey fan.
Without the first intro message, go directly to the reply. Go directly to the point and be short and clear.
Just start the reply directly with what has been asked, no messages like 'Sure!' and stuff - go straight to the point.
So withoyt the into message like The SQL query results reveal the... and stuff please!


"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that explains hockey stats."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=150,
    )
    return response.choices[0].message.content.strip()


class Question(BaseModel):
    question: str


@app.post("/ask")
def ask_question(data: Question):
    schema = get_table_schema()
    sql = question_to_sql(data.question, schema)
    result = pd.read_sql(sql, conn)
    summary = summarize_result(result)
    return {
        "sql": sql,
        "summary": summary,
        "data": result.to_dict(orient="records")
    }
