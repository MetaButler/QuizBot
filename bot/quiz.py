import random
import html
import requests
import psycopg2
from telegram import Update, Poll, Chat
from telegram.ext import CallbackContext
import logging
import configparser
from .database import create_tables
config = configparser.ConfigParser()
config.read('config.ini')

# Access the BOT_TOKEN
DATABASE_URL = config['database']['DATABASE_URL']

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def quiz(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    # Check if the command was invoked in a private chat
    if update.effective_chat.type != Chat.PRIVATE:
        update.message.reply_text("The /quiz command can only be used in DMs (private chats).")
        return

    try:
        # Randomly choose which API to use
        use_trivia_api = random.choice([True, False])  # Randomly select True or False
        if use_trivia_api:
            # Make an API call to get quiz questions from the trivia API
            api_url = 'https://the-trivia-api.com/api/questions/'
        else:
            # Use OpenTDB API as a fallback
            api_url = 'https://opentdb.com/api.php?amount=1'

        # Log the selected API
        logger.info(f"Using API: {api_url}")

        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()

        # Fetch the correct answer separately
        correct_answer = ""
        question = ""
        if not use_trivia_api and 'results' in data and data['results']:
            question = html.unescape(data['results'][0]['question'])
            correct_answer = html.unescape(data['results'][0]['correct_answer'])
        elif use_trivia_api and data and isinstance(data, list):
            selected_question = random.choice(data)
            question = selected_question.get('question', "")
            correct_answer = selected_question.get('correctAnswer', "")

        if not question or not correct_answer:
            logger.warning("No quiz questions found from the API.")
            update.message.reply_text("No quiz questions found from the API.")
            return

        # Fetch incorrect options (if available)
        incorrect_answers = []
        if not use_trivia_api and 'results' in data and data['results']:
            incorrect_answers = [html.unescape(option) for option in data['results'][0]['incorrect_answers']]
        elif use_trivia_api and data and isinstance(data, list):
            selected_question = random.choice(data)
            incorrect_answers = [html.unescape(option) for option in selected_question.get('incorrectAnswers', [])]

        # Construct options
        options = random.sample(incorrect_answers, min(3, len(incorrect_answers)))  # Randomly select up to 99 incorrect options
        options.append(correct_answer)  # Add the correct answer
        random.shuffle(options)  # Shuffle the options

        correct_option_id = options.index(correct_answer)

        # Send the quiz question as a poll
        update.message.reply_poll(
            question,
            options=options,
            type=Poll.QUIZ,
            correct_option_id=correct_option_id,
            is_anonymous=False
        )

    except requests.exceptions.RequestException as e:
        # Handle network or API errors
        logger.error(f"Failed to fetch quiz questions: {e}")
        update.message.reply_text("Failed to fetch quiz questions. Please try again later.")
        
def fetch_question_from_opentdb():
    api_url = f'https://opentdb.com/api.php?amount=1&category=26&type=boolean'
    response = requests.get(api_url)
    data = response.json()
    return data

def fetch_question_from_trivia_api():
    api_url = 'https://the-trivia-api.com/api/question/622a1c357cc59eab6f94fce0/'
    response = requests.get(api_url)
    data = response.json()
    return data

def process_question_from_opentdb(bot, chat_id, cursor, data, message_thread_id):
    conn = psycopg2.connect(DATABASE_URL)
    create_tables(conn)
    cursor = conn.cursor()
    
    if 'results' not in data or not data['results']:
        conn.close()
        return

    question_id = data['results'][0]['question']

    cursor.execute("SELECT 1 FROM sent_questions WHERE chat_id=%s AND question_id=%s", (chat_id, question_id))
    if cursor.fetchone():
        conn.close()
        return  # Question has been sent before

    question = html.unescape(data['results'][0]['question'])
    correct_answer = data['results'][0]['correct_answer']
    incorrect_answers = data['results'][0]['incorrect_answers']
    options = [html.unescape(option) for option in incorrect_answers] + [html.unescape(correct_answer)]
    random.shuffle(options)
    correct_option_id = options.index(html.unescape(correct_answer))

    message = bot.send_poll(chat_id, question, options, type=Poll.QUIZ, correct_option_id=correct_option_id, is_anonymous=False, message_thread_id=message_thread_id)
    poll = message.poll

    cursor.execute('''
        INSERT INTO sent_questions (chat_id, question_id) VALUES (%s, %s)
        ON CONFLICT (chat_id, question_id) DO NOTHING
    ''', (chat_id, question_id))

    cursor.execute('''
        INSERT INTO poll_answers (poll_id, chat_id, correct_option_id) VALUES (%s, %s, %s)
        ON CONFLICT (poll_id) DO UPDATE SET chat_id = EXCLUDED.chat_id, correct_option_id = EXCLUDED.correct_option_id
    ''', (poll.id, chat_id, correct_option_id))
    
    conn.commit()
    conn.close()

def process_question_from_trivia_api(bot, chat_id, cursor, data, message_thread_id):
    conn = psycopg2.connect(DATABASE_URL)
    create_tables(conn)
    cursor = conn.cursor()

    if not data or not isinstance(data, list):
        conn.close()
        return

    selected_question = random.choice(data)
    question_id = selected_question['id']

    cursor.execute("SELECT 1 FROM sent_questions WHERE chat_id=%s AND question_id=%s", (chat_id, question_id))
    if cursor.fetchone():
        conn.close()
        return  # Question has been sent before

    question = html.unescape(selected_question['question'])
    correct_answer = selected_question['correctAnswer']
    incorrect_answers = selected_question['incorrectAnswers']
    options = [html.unescape(option) for option in incorrect_answers] + [html.unescape(correct_answer)]
    random.shuffle(options)
    correct_option_id = options.index(html.unescape(correct_answer))

    message = bot.send_poll(chat_id, question, options, type=Poll.QUIZ, correct_option_id=correct_option_id, is_anonymous=False, message_thread_id=message_thread_id)
    poll = message.poll

    cursor.execute('''
        INSERT INTO sent_questions (chat_id, question_id) VALUES (%s, %s)
        ON CONFLICT (chat_id, question_id) DO NOTHING
    ''', (chat_id, question_id))

    cursor.execute('''
        INSERT INTO poll_answers (poll_id, chat_id, correct_option_id) VALUES (%s, %s, %s)
        ON CONFLICT (poll_id) DO UPDATE SET chat_id = EXCLUDED.chat_id, correct_option_id = EXCLUDED.correct_option_id
    ''', (poll.id, chat_id, correct_option_id))

    conn.commit()
    conn.close()

import random

def auto(bot, chat_id, cursor, message_thread_id):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        create_tables(conn)
        cursor = conn.cursor()

        total_retries = 0  # Total number of API retries
        max_retries = 3    # Maximum retries for each API

        while total_retries < 2 * max_retries:  # Two APIs, so double the max retries
            use_trivia_api = random.choice([True, False])  # Randomly choose an API

            if use_trivia_api:
                if total_retries // 2 < max_retries:  # Check if Trivia API retries are within limit
                    data = fetch_question_from_trivia_api()
                    if data and isinstance(data, list) and data:  # Check if data is a non-empty list
                        selected_question = random.choice(data)
                        question_id = selected_question['id']
                        cursor.execute("SELECT 1 FROM sent_questions WHERE chat_id=%s AND question_id=%s", (chat_id, question_id))
                        if cursor.fetchone():
                            logger.warning("Question already sent before from Trivia API")
                        else:
                            process_question_from_trivia_api(bot, chat_id, cursor, data, message_thread_id)
                            logger.info("Question successfully sent from Trivia API")
                            conn.commit()  # Commit changes to the database
                            return  # Question successfully sent
                    else:
                        logger.warning("Failed to fetch a question from Trivia API")
                else:
                    logger.warning("Exceeded Trivia API retry limit")
            else:
                if total_retries // 2 < max_retries:  # Check if OpenTDB retries are within limit
                    data = fetch_question_from_opentdb()
                    if data and 'results' in data and data['results']:
                        question_id = data['results'][0]['question']
                        cursor.execute("SELECT 1 FROM sent_questions WHERE chat_id=%s AND question_id=%s", (chat_id, question_id))
                        if cursor.fetchone():
                            logger.warning("Question already sent before from OpenTDB")
                        else:
                            process_question_from_opentdb(bot, chat_id, cursor, data, message_thread_id)
                            logger.info("Question successfully sent from OpenTDB")
                            conn.commit()  # Commit changes to the database
                            return  # Question successfully sent
                    else:
                        logger.warning("Failed to fetch a question from OpenTDB")
                else:
                    logger.warning("Exceeded OpenTDB retry limit")

            total_retries += 1

        # If no questions were successfully fetched, send a message
        bot.send_message(chat_id, "Sorry, No new question found")
        logger.warning("No new question found after retries")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        cursor.close()
        conn.close()


def send_auto_question(bot, context):
    conn = psycopg2.connect(DATABASE_URL)
    create_tables(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT chat_id, message_thread_id FROM group_preferences WHERE send_questions = TRUE")
    chat_ids_and_thread_ids = cursor.fetchall()

    for chat_id, message_thread_id in chat_ids_and_thread_ids:
        print(f"Sending auto quiz to chat_id: {chat_id}")
        
        # Check if a message_thread_id is available
        if message_thread_id:
            auto(bot, chat_id, cursor, message_thread_id)  # Send quiz to the specified message thread
        else:
            auto(bot, chat_id, cursor, chat_id)

    conn.close()
 