import psycopg2
from prettytable import PrettyTable
from telegram import Update
from telegram.ext import CallbackContext
import matplotlib.pyplot as plt
import numpy as np
import io
import configparser
config = configparser.ConfigParser()
config.read('config.ini')

# Access the BOT_TOKEN
DATABASE_URL = config['database']['DATABASE_URL']

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_preferences (
            chat_id BIGINT PRIMARY KEY,
            send_questions BOOLEAN DEFAULT TRUE,
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
    conn.commit()