from bot.database.models import GroupPreference
from sqlalchemy.orm import sessionmaker
from bot.helpers.yaml import load_config
from typing import Final
from sqlalchemy import create_engine
from telegram import Update, ChatMember
from telegram.ext import ContextTypes

# YAML Loader
db_config = load_config("config.yml")["database"]

# Constants
DB_SCHEMA: Final[str] = db_config.get("schema")

# Engine and Session
db_engine = create_engine(DB_SCHEMA)
Session = sessionmaker(bind=db_engine)

async def enablequiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    
    if chat.type == 'private':
        await message.reply_text(
            text="This command is not meant to be used in private chats!",
            reply_to_message_id=message.id,
            allow_sending_without_reply=True,
            quote=True
        )
        return

    chat_member = await context.bot.get_chat_member(
        chat_id=chat.id,
        user_id=user.id
    )
    
    if chat_member.status not in (ChatMember.ADMINISTRATOR, ChatMember.OWNER):
        await message.reply_text(
            text="Only administrators and owners can enable quiz",
            reply_to_message_id=message.id,
            message_thread_id=message.message_thread_id,
            quote=True,
            allow_sending_without_reply=True
        )
        return
    try:
        session = Session()
        group_preferences = session.query(GroupPreference).filter_by(chat_id=chat.id).first()
        if not group_preferences:
            group_preference = GroupPreference(chat_id=chat.id, send_questions=True, message_thread_id=message.message_thread_id)
            session.add(group_preference)
        else:
            group_preferences.send_questions = True
            group_preferences.message_thread_id = message.message_thread_id
        session.commit()
        await message.reply_text(
            text="Quiz enabled for this group!",
            reply_to_message_id=message.id,
            quote=True,
            allow_sending_without_reply=True
        )
    except Exception as ex:
        await message.reply_text(
            text="Some error occurred, please try again later!",
            reply_to_message_id=message.id,
            quote=True,
            allow_sending_without_reply=True,
        )
        print(f'Exception occurred in enablequiz: {ex}')
    finally:
        session.close()

async def disablequiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.type == 'private':
        await message.reply_text(
            text="This command is not meant to be used in private chats!",
            reply_to_message_id=message.id,
            allow_sending_without_reply=True,
            quote=True
        )
        return

    chat_member = await context.bot.get_chat_member(
        chat_id=chat.id,
        user_id=user.id
    )

    if chat_member.status not in (ChatMember.ADMINISTRATOR, ChatMember.OWNER):
        await message.reply_text(
            text="Only administrators and owners can disable quiz",
            reply_to_message_id=message.id,
            message_thread_id=message.message_thread_id,
            quote=True,
            allow_sending_without_reply=True
        )
        return
    try:
        session = Session()
        group_preference = session.query(GroupPreference).filter_by(chat_id=chat.id).first()
        if group_preference.send_questions:
            group_preference.send_questions = False
            session.commit()
            message_text = "Quiz has been disabled for this group"
        else:
            message_text = "Quiz is not enabled for this group."
        await message.reply_text(
            text=message_text,
            reply_to_message_id=message.id,
            quote=True,
            allow_sending_without_reply=True,
        )
    except Exception as ex:
        await message.reply_text(
            text="Some error occurred, please try again later!",
            reply_to_message_id=message.id,
            quote=True,
            allow_sending_without_reply=True,
        )
        print(f'Exception occurred in disablequiz: {ex}')
    finally:
        session.close()

async def quizstatus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if chat.type == 'private':
        await message.reply_text(
            text="This command is not meant to be used in private chats!",
            reply_to_message_id=message.id,
            allow_sending_without_reply=True,
            quote=True
        )
        return

    chat_member = await context.bot.get_chat_member(
        chat_id=chat.id,
        user_id=user.id,
    )

    if chat_member.status not in (ChatMember.ADMINISTRATOR, ChatMember.OWNER):
        await message.reply_text(
            text="Only administrators and owners can check status of quiz in this group",
            reply_to_message_id=message.id,
            allow_sending_without_reply=True,
            quote=True
        )
        return
    try:
        session = Session()
        group_preference = session.query(GroupPreference).filter_by(chat_id=chat.id).first()
        if not group_preference:
            message_text = "Quiz is not enabled in this group\n\nYou can enable quizzes with: /enablequiz"
        else:
            if group_preference.send_questions:
                message_text = "Quiz is enabled in this group"
            else:
                message_text = "Quiz is not enabled in this group\n\nYou can enable quizzes with: /enablequiz"
        await message.reply_text(
            text=message_text,
            reply_to_message_id=message.id,
            allow_sending_without_reply=True,
            quote=True
        )
    except Exception as ex:
        await message.reply_text(
                    text="Some error occurred, please try again later!",
                    reply_to_message_id=message.id,
                    quote=True,
                    allow_sending_without_reply=True,
                )
        print(f'Exception occurred in quizstatus: {ex}')
    finally:
        session.close()