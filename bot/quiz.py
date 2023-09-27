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

DATABASE_URL = config['database']['DATABASE_URL']

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def quiz(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    if update.effective_chat.type != Chat.PRIVATE:
        update.message.reply_text("The /quiz command can only be used in DMs (private chats).")
        return

    try:
        use_trivia_api = random.choice([True, False]) 
        if use_trivia_api:
            api_url = 'https://the-trivia-api.com/v2/questions'
        else:
            api_url = 'https://opentdb.com/api.php?amount=1'

        logger.info(f"Using API: {api_url}")

        response = requests.get(api_url)
        response.raise_for_status()

        data = response.json()

        correct_answer = ""
        question = ""
        incorrect_answers = []
        if not use_trivia_api and 'results' in data and data['results']:
            question = html.unescape(data['results'][0]['question'])
            correct_answer = html.unescape(data['results'][0]['correct_answer'])
            incorrect_answers = [html.unescape(option) for option in data['results'][0]['incorrect_answers']]
        elif use_trivia_api and data and isinstance(data, list):
            selected_question = random.choice(data)
            question = selected_question.get('question', {}).get('text', "")
            correct_answer = selected_question.get('correctAnswer', "")
            incorrect_answers = [html.unescape(option) for option in selected_question.get('incorrectAnswers', [])]

        if not question or not correct_answer or not incorrect_answers:
            logger.warning("No quiz questions found from the API.")
            update.message.reply_text("No quiz questions found from the API.")
            return

        options = random.sample(incorrect_answers, min(3, len(incorrect_answers)))
        options.append(correct_answer)
        random.shuffle(options)

        correct_option_id = options.index(correct_answer)

        update.message.reply_poll(
            question,
            options=options,
            type=Poll.QUIZ,
            correct_option_id=correct_option_id,
            is_anonymous=False
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch quiz questions: {e}")
        update.message.reply_text("Failed to fetch quiz questions. Please try again later.")
        
def fetch_question_from_opentdb():
    api_url = f'https://opentdb.com/api.php?amount=1'
    response = requests.get(api_url)
    data = response.json()
    return data

def fetch_question_from_trivia_api():
    api_url = 'https://the-trivia-api.com/v2/questions'
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
        return

    question = html.unescape(data['results'][0]['question'])
    correct_answer = data['results'][0]['correct_answer']
    incorrect_answers = data['results'][0]['incorrect_answers']
    
    # Limit options to 3
    options = [html.unescape(correct_answer)]  # Include the correct answer
    incorrect_answers = [html.unescape(option) for option in incorrect_answers]
    options.extend(random.sample(incorrect_answers, min(3, len(incorrect_answers))))  # Add 2 random incorrect options
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
        return

    question = html.unescape(selected_question['question']['text'])
    correct_answer = selected_question['correctAnswer']
    incorrect_answers = selected_question['incorrectAnswers']
    
    # Limit options to 3
    options = [html.unescape(correct_answer)]  # Include the correct answer
    incorrect_answers = [html.unescape(option) for option in incorrect_answers]
    options.extend(random.sample(incorrect_answers, min(3, len(incorrect_answers))))  # Add 2 random incorrect options
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

        total_retries = 0
        max_retries = 3

        while total_retries < 2 * max_retries:
            use_trivia_api = random.choice([True, False])

            if use_trivia_api:
                if total_retries // 2 < max_retries:
                    data = fetch_question_from_trivia_api()
                    if data and isinstance(data, list) and data:
                        selected_question = random.choice(data)
                        question_id = selected_question['id']
                        cursor.execute("SELECT 1 FROM sent_questions WHERE chat_id=%s AND question_id=%s", (chat_id, question_id))
                        if cursor.fetchone():
                            logger.warning("Question already sent before from Trivia API")
                        else:
                            process_question_from_trivia_api(bot, chat_id, cursor, data, message_thread_id)
                            logger.info("Question successfully sent from Trivia API")
                            conn.commit()
                            return
                    else:
                        logger.warning("Failed to fetch a question from Trivia API")
                else:
                    logger.warning("Exceeded Trivia API retry limit")
            else:
                if total_retries // 2 < max_retries:
                    data = fetch_question_from_opentdb()
                    if data and 'results' in data and data['results']:
                        question_id = data['results'][0]['question']
                        cursor.execute("SELECT 1 FROM sent_questions WHERE chat_id=%s AND question_id=%s", (chat_id, question_id))
                        if cursor.fetchone():
                            logger.warning("Question already sent before from OpenTDB")
                        else:
                            process_question_from_opentdb(bot, chat_id, cursor, data, message_thread_id)
                            logger.info("Question successfully sent from OpenTDB")
                            conn.commit()
                            return
                    else:
                        logger.warning("Failed to fetch a question from OpenTDB")
                else:
                    logger.warning("Exceeded OpenTDB retry limit")

            total_retries += 1

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
        
        if message_thread_id:
            auto(bot, chat_id, cursor, message_thread_id)
        else:
            auto(bot, chat_id, cursor, chat_id)

    conn.close()
 