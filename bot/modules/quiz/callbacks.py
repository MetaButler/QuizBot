from bot.modules.quiz.services import Session
from bot.database.models import GroupPreference
from telegram.ext import ContextTypes
from bot.modules.quiz.helpers import auto

async def send_auto_question_with_timeout(context: ContextTypes.DEFAULT_TYPE):
    timeout = int(context.job.data)
    session = Session()
    try:
        chat_preferences = session.query(GroupPreference).filter(GroupPreference.send_questions == True).all()
        for group in chat_preferences:
            group_settings = group.settings
            if group_settings:
                timer = int(group_settings.get("timer", 0))
            else:
                timer = 0
            
            if (timer == 0 and timeout == 3600) or timer == timeout:
                print(f"Sending auto quiz to chat_id: {group.chat_id}")
                message_thread_id = group.message_thread_id or group.chat_id
                await auto(context, group.chat_id, message_thread_id, group_settings)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        session.close()