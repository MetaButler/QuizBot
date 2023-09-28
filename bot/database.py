#Database.py

import psycopg2
import requests
import configparser
config = configparser.ConfigParser()
config.read('config.ini')

DATABASE_URL = config['database']['DATABASE_URL']

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_preferences (
            chat_id BIGINT PRIMARY KEY,
            send_questions BOOLEAN DEFAULT TRUE,
            trivia_topics TEXT,
            opentdb_topics TEXT,
            message_thread_id BIGINT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS poll_answers (
            poll_id TEXT PRIMARY KEY,
            chat_id BIGINT,
            correct_option_id INTEGER,
            FOREIGN KEY (chat_id) REFERENCES group_preferences(chat_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_scores (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            chat_id BIGINT,
            score REAL DEFAULT 0.0,
            correct_answers INTEGER DEFAULT 0,  -- New field for correct answers
            wrong_answers INTEGER DEFAULT 0,    -- New field for wrong answers
            UNIQUE (user_id, chat_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sent_questions (
            chat_id BIGINT,
            question_id TEXT,
            PRIMARY KEY (chat_id, question_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_scores (
            user_id BIGINT,
            chat_id BIGINT,
            score REAL DEFAULT 0.0,
            correct_answers INTEGER DEFAULT 0,
            wrong_answers INTEGER DEFAULT 0,
            UNIQUE (user_id, chat_id)
        )
    ''')
    cursor.execute("""
        DROP TABLE IF EXISTS topics;
        CREATE TABLE IF NOT EXISTS topics (
            category_id VARCHAR(255) PRIMARY KEY,
            category_name VARCHAR(255) NOT NULL,
            source VARCHAR(255) NOT NULL
        )
        """)    
    conn.commit()

def fetch_opentdb_categories(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        categories = []

        for category in data.get("trivia_categories", []):
            categories.append({"category_id": str(category["id"]), "category_name": category["name"], "source": "opentdb"})

        return categories
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch categories from {api_url}: {e}")
        return []

def fetch_the_trivia_categories(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        categories = []

        for category_name, subcategories in data.items():
            if subcategories:
                category_id = subcategories[0]
                categories.append({"category_id": category_id, "category_name": category_name, "source": "trivia"})

        return categories
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch categories from {api_url}: {e}")
        return []

def insert_categories_into_topics(categories):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        for category in categories:
            cursor.execute(f"INSERT INTO topics (category_id, category_name, source) VALUES (%s, %s, %s)",
                           (category["category_id"], category["category_name"], category["source"]))

        conn.commit()
        print(f"Inserted {len(categories)} categories into the 'topics' table.")
    except psycopg2.Error as e:
        print(f"Error inserting data into 'topics' table: {e}")
    finally:
        cursor.close()
        conn.close()