from telegram import Update, Chat
from telegram.ext import CallbackContext
import psycopg2
import configparser
from telegram import ChatMember
from .database import create_tables

config = configparser.ConfigParser()
config.read('config.ini')

DATABASE_URL = config['database']['DATABASE_URL']

def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    quiz_enabled = is_quiz_enabled(chat_id)

    if quiz_enabled:
        update.message.reply_text("Hi, I'm Alive!")
    else:
        update.message.reply_text("Hi, I'm Alive! Please enable the quiz by using /enablequiz.")

def enablequiz(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    message_thread_id = update.effective_message.message_thread_id
    user = update.effective_user

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        chat_member = context.bot.get_chat_member(chat_id, user.id)
        if chat_member.status not in (ChatMember.ADMINISTRATOR, ChatMember.CREATOR):
            update.message.reply_text("Only administrators can enable quizzes for this group.")
            return

        cursor.execute("""
            INSERT INTO group_preferences (chat_id, send_questions, message_thread_id) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (chat_id) 
            DO UPDATE SET send_questions = TRUE, message_thread_id = EXCLUDED.message_thread_id
        """, (chat_id, True, message_thread_id))
        conn.commit()
        update.message.reply_text("Quiz enabled for this group!")
    except Exception as e:
        conn.rollback()
        update.message.reply_text(f"An error occurred! Please Try Again")
    finally:
        conn.close()

def disablequiz(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user = update.effective_user

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        chat_member = context.bot.get_chat_member(chat_id, user.id)
        if chat_member.status not in (ChatMember.ADMINISTRATOR, ChatMember.CREATOR):
            update.message.reply_text("Only administrators can disable quizzes for this group.")
            return

        cursor.execute("""
            UPDATE group_preferences 
            SET send_questions = FALSE 
            WHERE chat_id = %s
        """, (chat_id,))
        conn.commit()
        update.message.reply_text("Quiz disabled for this group!")
    except Exception as e:
        conn.rollback()
        update.message.reply_text(f"An error occurred! Please Try Again")
    finally:
        conn.close()

def is_quiz_enabled(chat_id):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("SELECT send_questions FROM group_preferences WHERE chat_id = %s", (chat_id,))
    row = cursor.fetchone()

    conn.close()

    if row:
        return row[0]
    else:
        return False

def help(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    user_id = user.id

    chat_member = context.bot.get_chat_member(chat_id, user_id)

    commands = [
        ("/quiz", "Manually request a quiz in a private chat with the bot."),
        ("/rank", "View the top scorers in the group chat."),
        ("/score", "View your own quiz scores and statistics in the group chat."),
        ("/week", "View the top scorers in the group chat for the current week."),
    ]

    help_message = f"You can use the following commands:\n\n"

    for command, description in commands:
        help_message += f"<b>{command}:</b> {description}\n"

    if chat_member.status in (ChatMember.ADMINISTRATOR, ChatMember.CREATOR):
        help_message += "\nAdmin Commands:\n"
        help_message += "/enablequiz - Enable/Update the automatic quiz feature for the Group chat/ Thread\n"
        help_message += "/disablequiz - Disable the automatic quiz feature for the Group chat/Thread\n"
    
    update.message.reply_html(help_message)

def stats(update: Update, context: CallbackContext) -> None:
    allowed_user_id = 1999633661
    user_id = update.effective_user.id

    if user_id == allowed_user_id:
        conn = psycopg2.connect(DATABASE_URL)
        create_tables(conn)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM group_preferences")
        total_chats = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT user_id) FROM user_scores")
        total_users = cursor.fetchone()[0]

        conn.close()

        update.message.reply_text(f"Total Chats: {total_chats}\nTotal Users: {total_users}")
    else:
        update.message.reply_text("Sorry, you are not authorized to use this command.")

