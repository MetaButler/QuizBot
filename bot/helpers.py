from telegram import Update, Chat
from telegram.ext import CallbackContext
import psycopg2
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

# Access the BOT_TOKEN
DATABASE_URL = config['database']['DATABASE_URL']

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user

    if update.effective_chat.type == Chat.PRIVATE:
        update.message.reply_text("Hi, I'm Alive!. Send /quiz")
    else:
        update.message.reply_html("Hi, I'm Alive!\n\n")

def enable(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    message_thread_id = update.effective_message.message_thread_id  # Get the message_thread_id

    # Connect to the database
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # Insert data into the group_preferences table or update if it already exists
        cursor.execute("""
            INSERT INTO group_preferences (chat_id, send_questions, message_thread_id) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (chat_id) 
            DO UPDATE SET send_questions = EXCLUDED.send_questions, message_thread_id = EXCLUDED.message_thread_id
        """, (chat_id, True, message_thread_id))
        conn.commit()
        update.message.reply_text("Quiz enabled for this group!")
    except Exception as e:
        conn.rollback()
        update.message.reply_text(f"An error occurred: {e}")
    finally:
        conn.close()

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

