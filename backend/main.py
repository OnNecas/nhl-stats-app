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


def ask_with_summary(question, schema):
    # Step 1: Generate SQL from question
    sql_prompt = f"""
You are an assistant that converts natural language into SQL queries.

The table 'players' has the following columns:
{schema}

Use these rules:
- 'situation' column has values like 'all', '5on5', '5on4', etc.
- If no specific situation is mentioned, default to situation='all'
- 'powerplay' = rows with situation in ('5on4', '5on3', '4on3')
- Use 'I_F_Goals' for goals
- For "icetime", return SUM()
- Player names should be Title Case (e.g., 'zach werenski' -> 'Zach Werenski')
- For top players, return top 10 rows and include both names and stat columns
- return always 10 records, not only the best one.

Return only the SQL query.
Question: {question}
"""

    sql_response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # or "gpt-3.5-turbo" if needed
        messages=[
            {"role": "system", "content": "You are an expert SQL generator."},
            {"role": "user", "content": sql_prompt}
        ],
        temperature=0.3,
        max_tokens=150,
    )

    sql = sql_response.choices[0].message.content.strip()

    # Step 2: Run SQL
    try:
        result = pd.read_sql(sql, conn)
    except Exception as e:
        return {"error": str(e), "sql": sql}

    # Step 3: Generate summary from results
    summary_prompt = f"""
The user asked: {question}

The SQL query returned the following result:
{result.to_string(index=False)}

Please summarize the answer in one short, clear sentence for a hockey fan.
Skip the intro like "The results show..." — go straight to the point.
"""

    summary_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for summarizing hockey stats."},
            {"role": "user", "content": summary_prompt}
        ],
        temperature=0.7,
        max_tokens=150,
    )

    summary = summary_response.choices[0].message.content.strip()

    return {
        "sql": sql,
        "summary": summary,
        "data": result.to_dict(orient="records")
    }


class Question(BaseModel):
    question: str


@app.post("/ask")
def ask_question(data: Question):
    schema = get_table_schema()
    return ask_with_summary(data.question, schema)
