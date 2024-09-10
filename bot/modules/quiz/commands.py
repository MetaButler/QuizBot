from bot.database.models import GroupPreference
from sqlalchemy.orm import sessionmaker
from bot.helpers.yaml import load_config
from typing import Final
from sqlalchemy import create_engine
from telegram import Update, ChatMember, Poll
from telegram.ext import ContextTypes
from bot.helpers.http import fetch_quiz_question
from bot.helpers.misc import get_start_time

# YAML Loader
db_config = load_config("config.yml")["database"]

# Constants
DB_SCHEMA: Final[str] = db_config.get("schema")

# Engine and Session
db_engine = create_engine(DB_SCHEMA)
Session = sessionmaker(bind=db_engine)


async def enablequiz(update: Update,
                     context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    if int(message.date.timestamp()) < get_start_time():
        return

    if chat.type == 'private':
        await message.reply_text(
            text="This command is not meant to be used in private chats!",
            reply_to_message_id=message.id,
            quote=True)
        return

    chat_member = await context.bot.get_chat_member(chat_id=chat.id,
                                                    user_id=user.id)

    if chat_member.status not in (ChatMember.ADMINISTRATOR, ChatMember.OWNER):
        await message.reply_text(
            text="Only administrators and owners can enable quiz",
            reply_to_message_id=message.id,
            message_thread_id=message.message_thread_id,
            quote=True,
        )
        return
    session = Session()
    try:
        group_preferences = session.query(GroupPreference).filter_by(
            chat_id=chat.id).first()
        if not group_preferences:
            group_preference = GroupPreference(
                chat_id=chat.id,
                send_questions=True,
                message_thread_id=message.message_thread_id)
            session.add(group_preference)
        else:
            group_preferences.send_questions = True
            group_preferences.message_thread_id = message.message_thread_id
        session.commit()
        await message.reply_text(
            text="Quiz enabled for this group!",
            reply_to_message_id=message.id,
            quote=True,
        )
    except Exception as ex:
        await message.reply_text(
            text="Some error occurred, please try again later!",
            reply_to_message_id=message.id,
            quote=True,
        )
        print(f'Exception occurred in enablequiz: {ex}')
    finally:
        session.close()


async def disablequiz(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    if int(message.date.timestamp()) < get_start_time():
        return

    if chat.type == 'private':
        await message.reply_text(
            text="This command is not meant to be used in private chats!",
            reply_to_message_id=message.id,
            quote=True)
        return

    chat_member = await context.bot.get_chat_member(chat_id=chat.id,
                                                    user_id=user.id)

    if chat_member.status not in (ChatMember.ADMINISTRATOR, ChatMember.OWNER):
        await message.reply_text(
            text="Only administrators and owners can disable quiz",
            reply_to_message_id=message.id,
            message_thread_id=message.message_thread_id,
            quote=True,
        )
        return
    session = Session()
    try:
        group_preference = session.query(GroupPreference).filter_by(
            chat_id=chat.id).first()
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
        )
    except Exception as ex:
        await message.reply_text(
            text="Some error occurred, please try again later!",
            reply_to_message_id=message.id,
            quote=True,
        )
        print(f'Exception occurred in disablequiz: {ex}')
    finally:
        session.close()


async def quizstatus(update: Update,
                     context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    if int(message.date.timestamp()) < get_start_time():
        return

    if chat.type == 'private':
        await message.reply_text(
            text="This command is not meant to be used in private chats!",
            reply_to_message_id=message.id,
            quote=True)
        return

    chat_member = await context.bot.get_chat_member(
        chat_id=chat.id,
        user_id=user.id,
    )

    if chat_member.status not in (ChatMember.ADMINISTRATOR, ChatMember.OWNER):
        await message.reply_text(
            text=
            "Only administrators and owners can check status of quiz in this group",
            reply_to_message_id=message.id,
            quote=True)
        return
    session = Session()
    try:
        group_preference = session.query(GroupPreference).filter_by(
            chat_id=chat.id).first()
        if not group_preference:
            message_text = "Quiz is not enabled in this group\n\nYou can enable quizzes with: /enablequiz"
        else:
            if group_preference.send_questions:
                message_text = "Quiz is enabled in this group"
            else:
                message_text = "Quiz is not enabled in this group\n\nYou can enable quizzes with: /enablequiz"
        await message.reply_text(text=message_text,
                                 reply_to_message_id=message.id,
                                 quote=True)
    except Exception as ex:
        await message.reply_text(
            text="Some error occurred, please try again later!",
            reply_to_message_id=message.id,
            quote=True,
        )
        print(f'Exception occurred in quizstatus: {ex}')
    finally:
        session.close()


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message
    if int(message.date.timestamp()) < get_start_time():
        return

    if chat.type != "private":
        await message.reply_text(
            text="This command can only be used in private chats!",
            quote=True,
            reply_to_message_id=message.id)
        return
    await context.bot.send_chat_action(chat_id=chat.id, action='typing')
    quiz_data = await fetch_quiz_question()
    if quiz_data:
        question = quiz_data["question"]
        options = quiz_data["options"]
        correct_option_id = quiz_data["correct_option_id"]
        await message.reply_poll(
            question=question,
            options=options,
            is_anonymous=False,
            correct_option_id=correct_option_id,
            type=Poll.QUIZ,
        )
    else:
        await message.reply_text(
            text="Failed to fetch quiz questions. Please try again later.",
            quote=True,
            reply_to_message_id=message.id)
