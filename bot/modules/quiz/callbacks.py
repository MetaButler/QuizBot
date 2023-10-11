from bot.modules.quiz.services import Session
from bot.database.models import GroupPreference
from telegram.ext import ContextTypes
from bot.modules.quiz.helpers import auto

async def send_auto_question_no_timeout_or_3600_timeout(context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    try:
        chat_preferences = session.query(GroupPreference).filter(GroupPreference.send_questions == True).all()
        for group in chat_preferences:
            if (group.settings and int(group.settings["timer"]) == 3600) or group.settings is None:
                print(f"Sending auto quiz to chat_id: {group.chat_id}")
                if group.message_thread_id:
                    await auto(context, group.chat_id, group.message_thread_id, group.settings)
                else:
                    await auto(context, group.chat_id, group.chat_id, group.settings)
    except Exception as e:
        print(f"An error occurred: {e}")

async def send_auto_question_900_timeout(context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    try:
        chat_preferences = session.query(GroupPreference).filter(GroupPreference.send_questions == True).all()
        for group in chat_preferences:
            if group.settings and int(group.settings["timer"]) == 900:
                print(f"Sending auto quiz to chat_id: {group.chat_id}")
                if group.message_thread_id:
                    await auto(context, group.chat_id, group.message_thread_id, group.settings)
                else:
                    await auto(context, group.chat_id, group.chat_id, group.settings)
    except Exception as e:
        print(f"An error occurred: {e}")

async def send_auto_question_1800_timeout(context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    try:
        chat_preferences = session.query(GroupPreference).filter(GroupPreference.send_questions == True).all()
        for group in chat_preferences:
            if group.settings and int(group.settings["timer"]) == 1800:
                print(f"Sending auto quiz to chat_id: {group.chat_id}")
                if group.message_thread_id:
                    await auto(context, group.chat_id, group.message_thread_id, group.settings)
                else:
                    await auto(context, group.chat_id, group.chat_id, group.settings)
    except Exception as e:
        print(f"An error occurred: {e}")

async def send_auto_question_2700_timeout(context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    try:
        chat_preferences = session.query(GroupPreference).filter(GroupPreference.send_questions == True).all()
        for group in chat_preferences:
            if group.settings and int(group.settings["timer"]) == 2700:
                print(f"Sending auto quiz to chat_id: {group.chat_id}")
                if group.message_thread_id:
                    await auto(context, group.chat_id, group.message_thread_id, group.settings)
                else:
                    await auto(context, group.chat_id, group.chat_id, group.settings)
    except Exception as e:
        print(f"An error occurred: {e}")

async def send_auto_question_5400_timeout(context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    try:
        chat_preferences = session.query(GroupPreference).filter(GroupPreference.send_questions == True).all()
        for group in chat_preferences:
            if group.settings and int(group.settings["timer"]) == 5400:
                print(f"Sending auto quiz to chat_id: {group.chat_id}")
                if group.message_thread_id:
                    await auto(context, group.chat_id, group.message_thread_id, group.settings)
                else:
                    await auto(context, group.chat_id, group.chat_id, group.settings)
    except Exception as e:
        print(f"An error occurred: {e}")

async def send_auto_question_7200_timeout(context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    try:
        chat_preferences = session.query(GroupPreference).filter(GroupPreference.send_questions == True).all()
        for group in chat_preferences:
            if group.settings and int(group.settings["timer"]) == 7200:
                print(f"Sending auto quiz to chat_id: {group.chat_id}")
                if group.message_thread_id:
                    await auto(context, group.chat_id, group.message_thread_id, group.settings)
                else:
                    await auto(context, group.chat_id, group.chat_id, group.settings)
    except Exception as e:
        print(f"An error occurred: {e}")