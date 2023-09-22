import requests
import random
import html
import psycopg2
import time
import logging
import io
import matplotlib.pyplot as plt
import numpy as np
import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler

from prettytable import PrettyTable
from telegram import Poll, Update, Chat
from telegram.ext import Updater, CommandHandler, CallbackContext, PollAnswerHandler, Filters

scheduler = BackgroundScheduler(timezone=pytz.utc)  # Use UTC as an example

DATABASE_URL = "postgresql://zpmvqpmx:dRSGqOJ9XGBt_XExTeIATnbwKBPC4zRF@fanny.db.elephantsql.com/zpmvqpmx"


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_preferences (
            chat_id BIGINT PRIMARY KEY,
            send_questions BOOLEAN DEFAULT TRUE
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

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id

    if update.effective_chat.type == Chat.PRIVATE:
        update.message.reply_text("Hi, I'm Alive!. Send /quiz")
    else:
        chat_member = context.bot.get_chat_member(chat_id, user_id)

        conn = psycopg2.connect(DATABASE_URL)
        create_tables(conn)
        cursor = conn.cursor()

        cursor.execute("INSERT INTO group_preferences (chat_id, send_questions) VALUES (%s, %s) ON CONFLICT (chat_id) DO NOTHING",
                       (chat_id, True))
        conn.commit()
        conn.close()

        update.message.reply_html("Hi, I'm Alive!\n\n")


def help(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id

    chat_member = context.bot.get_chat_member(chat_id, user_id)

    update.message.reply_html(
        "🤖 I'm your quiz bot!\n\n"
        "You can use the following commands:\n"
        "I will automatically send quizzes to this group every 60 minutes.\n"
        "Enjoy the quizzes!\n\n"
        "👥 <b>Send /start for quizzes</b>"
    )

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
    api_url = f'https://opentdb.com/api.php?amount=1'
    response = requests.get(api_url)
    data = response.json()
    return data

def fetch_question_from_trivia_api():
    api_url = 'https://the-trivia-api.com/api/questions/'
    response = requests.get(api_url)
    data = response.json()
    return data

def process_question_from_opentdb(bot, chat_id, cursor, data):
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

    message = bot.send_poll(chat_id, question, options, type=Poll.QUIZ, correct_option_id=correct_option_id, is_anonymous=False)
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

def process_question_from_trivia_api(bot, chat_id, cursor, data):
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

    message = bot.send_poll(chat_id, question, options, type=Poll.QUIZ, correct_option_id=correct_option_id, is_anonymous=False)
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

def auto(bot, chat_id, cursor):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        create_tables(conn)
        cursor = conn.cursor()

        for _ in range(2):  # Retry twice
            if random.choice([True, False]):  # Randomly choose an API
                data = fetch_question_from_opentdb()
                if data and 'results' in data and data['results']:
                    question_id = data['results'][0]['question']
                    cursor.execute("SELECT 1 FROM sent_questions WHERE chat_id=%s AND question_id=%s", (chat_id, question_id))
                    if cursor.fetchone():
                        logger.warning("Question already sent before from OpenTDB")
                    else:
                        process_question_from_opentdb(bot, chat_id, cursor, data)
                        logger.info("Question successfully sent from OpenTDB")
                        conn.commit()  # Commit changes to the database
                        return  # Question successfully sent
                else:
                    logger.warning("Failed to fetch a question from OpenTDB")
            else:
                data = fetch_question_from_trivia_api()
                if data and isinstance(data, list) and data:  # Check if data is a non-empty list
                    selected_question = random.choice(data)
                    question_id = selected_question['id']
                    cursor.execute("SELECT 1 FROM sent_questions WHERE chat_id=%s AND question_id=%s", (chat_id, question_id))
                    if cursor.fetchone():
                        logger.warning("Question already sent before from Trivia API")
                    else:
                        process_question_from_trivia_api(bot, chat_id, cursor, data)
                        logger.info("Question successfully sent from Trivia API")
                        conn.commit()  # Commit changes to the database
                        return  # Question successfully sent
                else:
                    logger.warning("Failed to fetch a question from Trivia API")

        # If both APIs fail or the question is already in the database, send "Sorry, No new question found" message
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

    cursor.execute("SELECT chat_id FROM group_preferences WHERE send_questions = TRUE")
    chat_ids = [row[0] for row in cursor.fetchall()]

    conn.close()

    for chat_id in chat_ids:
        print(f"Sending auto quiz to chat_id: {chat_id}")
        auto(bot, chat_id, cursor) 

def log_user_response(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = user.id
    poll_id = update.poll_answer.poll_id
    option_id = update.poll_answer.option_ids[0]

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute('SELECT chat_id, correct_option_id FROM poll_answers WHERE poll_id = %s', (poll_id,))
    row = cursor.fetchone()

    if row:
        chat_id, correct_option_id = row
        if correct_option_id == option_id:
            # User answered correctly
            cursor.execute('INSERT INTO user_scores (user_id, chat_id, score, correct_answers) VALUES (%s, %s, 1, 1) ON CONFLICT (user_id, chat_id) DO UPDATE SET score = user_scores.score + 1, correct_answers = user_scores.correct_answers + 1',
                           (user_id, chat_id))
            cursor.execute('INSERT INTO weekly_scores (user_id, chat_id, score, correct_answers) VALUES (%s, %s, 1, 1) ON CONFLICT (user_id, chat_id) DO UPDATE SET score = weekly_scores.score + 1, correct_answers = weekly_scores.correct_answers + 1',
                           (user_id, chat_id))
        else:
            # User answered incorrectly
            cursor.execute('INSERT INTO user_scores (user_id, chat_id, score, wrong_answers) VALUES (%s, %s, -0.5, 1) ON CONFLICT (user_id, chat_id) DO UPDATE SET score = user_scores.score - 0.5, wrong_answers = user_scores.wrong_answers + 1',
                           (user_id, chat_id))
            cursor.execute('INSERT INTO weekly_scores (user_id, chat_id, score, wrong_answers) VALUES (%s, %s, -0.5, 1) ON CONFLICT (user_id, chat_id) DO UPDATE SET score = weekly_scores.score - 0.5, wrong_answers = weekly_scores.wrong_answers + 1',
                           (user_id, chat_id))

        conn.commit()

    conn.close()


def get_top_scores(chat_id, limit=5):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_id, score
        FROM user_scores
        WHERE chat_id = %s
        ORDER BY score DESC
        LIMIT %s
    ''', (chat_id, limit))

    top_scores = cursor.fetchall()

    conn.close()

    return top_scores

def rank(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    top_scores = get_top_scores(chat_id)

    if not top_scores:
        update.message.reply_text("No scores found for this chat.")
        return

    message = "Top Score Holders:\n"
    for i, (user_id, score) in enumerate(top_scores, start=1):
        user = context.bot.get_chat_member(chat_id, user_id).user
        if i == 1:
            trophy = "🏆"
        elif i == 2:
            trophy = "🥈"
        elif i == 3:
            trophy = "🥉" 
        else:
            trophy = "🏅"
        
        username = f"{user.first_name}: {score}".ljust(20)
        message += f"{trophy}{username}\n"

    update.message.reply_text(message)

def weekly_rank(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    top_weekly_scores = get_top_weekly_scores(chat_id)

    if not top_weekly_scores:
        update.message.reply_text("No weekly scores found for this chat.")
        return

    message = "Weekly Score Holders:\n"
    for i, (user_id, score) in enumerate(top_weekly_scores, start=1):
        user = context.bot.get_chat_member(chat_id, user_id).user
        if i == 1:
            trophy = "🏆"
        elif i == 2:
            trophy = "🥈"
        elif i == 3:
            trophy = "🥉"
        else:
            trophy = "🏅"

        username = f"{user.first_name}: {score:.2f}".ljust(20)
        message += f"{trophy}{username}\n"

    update.message.reply_text(message)

def get_top_weekly_scores(chat_id, limit=5):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_id, score
        FROM weekly_scores
        WHERE chat_id = %s
        ORDER BY score DESC
        LIMIT %s
    ''', (chat_id, limit))

    top_weekly_scores = cursor.fetchall()

    conn.close()

    return top_weekly_scores

def score(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    userid = str(user.id)
    user_id = f"{' ' * (10 - len(userid))}{userid}" if len(userid) < 10 else userid[:10]
    username = user.first_name[:15]  # Change this to get the desired name field
    user_name = f"{username}{' ' * (15 - len(username))}" if len(username) < 15 else username[:15]
    
    conn = psycopg2.connect(DATABASE_URL)
    create_tables(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT score, correct_answers, wrong_answers FROM user_scores WHERE chat_id = %s AND user_id = %s", (chat_id, user_id))
    row = cursor.fetchone()

    if row:
        user_score, correct_answers, wrong_answers = row
        accuracy = (correct_answers / (correct_answers + wrong_answers)) * 100 if correct_answers + wrong_answers > 0 else 0

        # Create a PrettyTable instance
        table = PrettyTable()
        table.field_names = [user_name, user_id]
        table.align[user_name] = "l"
        table.align[user_id] = "r"
        table.add_row(["Your Score", f"{user_score:.2f}"])
        table.add_row(["Correct Answers", str(correct_answers)])
        table.add_row(["Wrong Answers", str(wrong_answers)])
        table.add_row(["Accuracy", f"{accuracy:.2f}%"])

        # Get the table as a string
        table_str = table.get_string()

        update.message.reply_text(f"```\n{table_str}\n```", parse_mode="Markdown")
    else:
        update.message.reply_text("Your Score: Go Answer Some Questions")

    conn.close()

def score_dm_total(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = user.id

    conn = psycopg2.connect(DATABASE_URL)
    create_tables(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(score), SUM(correct_answers), SUM(wrong_answers) FROM user_scores WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()

    conn.close()

    if row:
        total_score, total_correct_answers, total_wrong_answers = row
        total_accuracy = (total_correct_answers / (total_correct_answers + total_wrong_answers)) * 100 if total_correct_answers + total_wrong_answers > 0 else 0

        # Create a bar chart
        labels = ['Correct Answers', 'Wrong Answers']
        values = [total_correct_answers, total_wrong_answers]
        x = np.arange(len(labels))
        width = 0.35

        fig, ax = plt.subplots()
        rects = ax.bar(x, values, width, label='Count')

        ax.set_xlabel('Category')
        ax.set_ylabel('Count')
        ax.set_title('Total Answers Distribution')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()

        # Add data labels to the bars
        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom')

        # Add accuracy to the caption
        caption = f"Total Score Across Chats: {total_score}\nAccuracy: {total_accuracy:.2f}%"

        # Save the bar chart to a byte buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)

        # Send the bar chart as a photo with the updated caption
        update.message.reply_photo(photo=io.BufferedReader(buffer), caption=caption)

        plt.close()
    else:
        update.message.reply_text("Your Total Score: 0")

def stats(update: Update, context: CallbackContext) -> None:
    allowed_user_id = 1999633661  # Replace with the specific user_id allowed to use the command
    user_id = update.effective_user.id

    if user_id == allowed_user_id:
        conn = psycopg2.connect(DATABASE_URL)
        create_tables(conn)
        cursor = conn.cursor()

        # Get total chats from group_preferences
        cursor.execute("SELECT COUNT(*) FROM group_preferences")
        total_chats = cursor.fetchone()[0]

        # Get total unique users from user_scores
        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_scores")
        total_users = cursor.fetchone()[0]

        conn.close()

        update.message.reply_text(f"Total Chats: {total_chats}\nTotal Users: {total_users}")
    else:
        update.message.reply_text("Sorry, you are not authorized to use this command.")

def reset_weekly_scores():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Reset the "weekly_scores" table for the current week
    cursor.execute(
        "UPDATE weekly_scores "
        "SET score = 0, correct_answers = 0, wrong_answers = 0"
    )

    conn.commit()
    conn.close()


def main() -> None:
    updater = Updater("5852350596:AAG2GW5-BW9ekRDRvyZ91a66uIjJqYg5o5A", use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(PollAnswerHandler(log_user_response))
    dispatcher.add_handler(CommandHandler("rank", rank)) 
    dispatcher.add_handler(CommandHandler("score", score, Filters.chat_type.groups))
    dispatcher.add_handler(CommandHandler("score", score_dm_total, Filters.chat_type.private))    
    dispatcher.add_handler(CommandHandler("quiz", quiz))
    dispatcher.add_handler(CommandHandler("stats", stats))
    dispatcher.add_handler(CommandHandler("week", weekly_rank))

    job_queue = updater.job_queue
    send_auto_question_with_bot = lambda context: send_auto_question(updater.bot, context)
    job_queue.run_once(send_auto_question_with_bot, 10)  # Run once after 60 seconds    
    job_queue.run_repeating(send_auto_question_with_bot, interval=50)
    scheduler.add_job(reset_weekly_scores, 'cron', day_of_week='sun', hour=0, minute=0, second=0, timezone=pytz.utc)

    # Start the scheduler
    scheduler.start()

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
