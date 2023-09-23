from telegram.ext import CommandHandler, PollAnswerHandler, Filters
from telegram import Update, Chat
from telegram.ext import Updater, CallbackContext
from .helpers import start, help, stats, enablequiz, disablequiz
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import psycopg2
from .quiz import quiz, send_auto_question
from .database import create_tables
from .score import reset_weekly_scores, log_user_response, rank, score, score_dm_total, weekly_rank
import configparser

scheduler = BackgroundScheduler(timezone=pytz.utc)

config = configparser.ConfigParser()
config.read('config.ini')

DATABASE_URL = config['database']['DATABASE_URL']
BOT_TOKEN = config['bot']['BOT_TOKEN']

def main() -> None:
    updater = Updater(BOT_TOKEN, use_context=True)
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
    dispatcher.add_handler(CommandHandler("enablequiz", enablequiz, Filters.chat_type.groups))
    dispatcher.add_handler(CommandHandler("disablequiz", disablequiz, Filters.chat_type.groups))

    try:
        conn = psycopg2.connect(DATABASE_URL)
        create_tables(conn)
        conn.close()
        print("Database tables created successfully.")
    except Exception as e:
        print(f"Error creating database tables: {e}")

    job_queue = updater.job_queue
    send_auto_question_with_bot = lambda context: send_auto_question(updater.bot, context)
    job_queue.run_once(send_auto_question_with_bot, 1800)    
    job_queue.run_repeating(send_auto_question_with_bot, interval=3600)
    scheduler.add_job(reset_weekly_scores, 'cron', day_of_week='sun', hour=0, minute=0, second=0, timezone=pytz.utc)

    scheduler.start()

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
