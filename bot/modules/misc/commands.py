from typing import Final, List

from telegram import (ChatMember, InlineKeyboardButton, InlineKeyboardMarkup,
                      Update)
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.helpers.misc import get_start_time
from bot.helpers.yaml import load_config
from bot.modules.misc.services import get_bot_stats, get_recent_stats
from bot.modules.quiz.services import is_quiz_enabled

# YAML Loader
telegram_config = load_config("config.yml")["telegram"]

# Constants
AUTHORIZED_IDS: Final[List[int]] = [
    int(telegram_id) for telegram_id in telegram_config["authorized_ids"]
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_type = update.message.chat.type
    message = update.effective_message
    if int(message.date.timestamp()) < get_start_time():
        return
    if chat_type == 'private':
        await update.message.reply_text(
            text=
            "Hi, I'm alive! To get a quiz, press: /quiz\n\nIf you want to use this bot in a group for auto quizzes, you can add me to your group by clicking the button below.",
            reply_to_message_id=update.message.id,
            quote=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "Add to group",
                    url=f"https://t.me/{context.bot.username}?startgroup=start"
                )
            ]]))
    else:
        message_text = ""
        if is_quiz_enabled(chat_id=update.effective_chat.id):
            message_text = "Hi, I'm alive!"
        else:
            message_text = "Hi, I'm alive! Please enable the quiz functionality with: /enablequiz.\nI will send a quiz at your specified schedule (default, 1 hour)"
        await update.message.reply_text(
            text=message_text,
            reply_to_message_id=update.message.id,
            quote=True,
        )


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.effective_message
    chat = update.effective_chat
    if int(message.date.timestamp()) < get_start_time():
        return
    chat_member = await context.bot.get_chat_member(chat_id=chat.id,
                                                    user_id=user.id)
    commands = {
        'quiz': {
            'description':
            'Manually request a quiz in a private chat with the bot.',
            'admin_only': False,
            'dev_only': False,
        },
        'rank': {
            'description': 'View the top scorers in the group chat.',
            'admin_only': False,
            'dev_only': False,
        },
        'score': {
            'description':
            'View your own quiz scores and statistics in the group chat.',
            'admin_only': False,
            'dev_only': False,
        },
        'week': {
            'description':
            'View the top scorers in the group chat for the current week.',
            'admin_only': False,
            'dev_only': False,
        },
        'settings': {
            'description': 'Change the user\'s settings on a global level',
            'admin_only': False,
            'dev_only': False,
        },
        'enablequiz': {
            'description':
            'Enable/Update the automatic quiz feature for the Group chat/Thread',
            'admin_only': True,
            'dev_only': False,
        },
        'disablequiz': {
            'description':
            'Disable the automatic quiz feature for the Group chat/Thread',
            'admin_only': True,
            'dev_only': False,
        },
        'quizstatus': {
            'description': 'Check status of quiz in the group chat/thread',
            'admin_only': True,
            'dev_only': False,
        },
        'stats': {
            'description':
            'Get bot stats, including number of users and groups',
            'admin_only': False,
            'dev_only': True,
        }
    }

    help_message = ""
    for command, body in commands.items():
        if not (body.get('admin_only') or body.get('dev_only')):
            help_message += f'<b>/{command}</b>: {body.get("description")}\n'
        else:
            if chat.type in ('group', 'supergroup'):
                if body.get('admin_only') and chat_member.status in (
                        ChatMember.OWNER, ChatMember.ADMINISTRATOR):
                    help_message += f'\n<b>/{command}</b>: {body.get("description")} (<u>ADMIN ONLY</u>)'
                elif body.get('dev_only') and user.id in AUTHORIZED_IDS:
                    help_message += f'\n<b>/{command}</b>: {body.get("description")} (<u>DEV ONLY</u>)'
    await update.message.reply_html(
        text=help_message,
        reply_to_message_id=message.id,
        quote=True,
    )


async def stats(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    if int(message.date.timestamp()) < get_start_time():
        return

    if user.id not in AUTHORIZED_IDS:
        await message.reply_text(text="This command is not meant for you",
                                 reply_to_message_id=message.id,
                                 quote=True)
        return
    chat_stats, user_stats = get_bot_stats()
    if chat_stats is None or user_stats is None:
        message_text = 'Failed to obtain stats!'
    else:
        message_text = f'<b>Global Stats:</b>\nTotal Chats: {chat_stats}\nTotal Users: {user_stats}'

    user_row_count, chat_row_count = get_recent_stats()
    message_text += f'\n\n<b>Last 24H Stats:</b>\nChat Count: {chat_row_count}\nUser Count: {user_row_count}'

    await message.reply_text(
        text=message_text,
        reply_to_message_id=message.id,
        quote=True,
        parse_mode=ParseMode.HTML,
    )
