from bot.modules.quiz.services import Session
from bot.database.models import GroupPreference
from telegram.ext import ContextTypes
from bot.modules.quiz.helpers import auto

async def send_auto_question(context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    try:
        chat_preferences = session.query(GroupPreference).filter(GroupPreference.send_questions == True).all()
        for preference in chat_preferences:
            print(f"Sending auto quiz to chat_id: {preference.chat_id}")
            if preference.message_thread_id:
                await auto(context, preference.chat_id, preference.message_thread_id)
            else:
                await auto(context, preference.chat_id, preference.chat_id)
    except Exception as e:
        print(f"An error occurred: {e}")