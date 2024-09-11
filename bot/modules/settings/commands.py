from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ContextTypes
from bot.modules.settings.services import get_user_global_config, set_user_global_config, set_chat_config, get_chat_config
from bot.helpers.misc import get_start_time


async def settings_dm(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_chat
    message = update.effective_message
    if int(message.date.timestamp()) < get_start_time():
        return

    user_settings = await get_user_global_config(user_id=user.id)
    if user_settings is None:
        settings = {
            'ui': 'light',
            'privacy': 'off',
        }
        await set_user_global_config(
            user_id=user.id,
            settings=settings,
        )
        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(
                    f'UI Color: {settings.get("ui").capitalize()}',
                    callback_data=f'stngs_ui_{user.id}'),
            ],
             [
                 InlineKeyboardButton(
                     f'Privacy: {settings.get("privacy").capitalize()}',
                     callback_data=f'stngs_prvcy_{user.id}')
             ]])
    else:
        keyboard = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton(
                    f'UI Color: {user_settings.get("ui").capitalize()}',
                    callback_data=f'stngs_ui_{user.id}'),
            ],
             [
                 InlineKeyboardButton(
                     f'Privacy: {user_settings.get("privacy").capitalize()}',
                     callback_data=f'stngs_prvcy_{user.id}')
             ]])
    await message.reply_text(text="Here are your global settings:",
                             reply_to_message_id=message.id,
                             quote=True,
                             reply_markup=keyboard)


async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    if int(message.date.timestamp()) < get_start_time():
        return

    chat_member = await context.bot.get_chat_member(chat_id=chat.id,
                                                    user_id=user.id)
    if chat_member.status not in (ChatMember.ADMINISTRATOR, ChatMember.OWNER):
        await message.reply_text(
            text=
            "Only administrators and owners can change group settings for quizzes",
            reply_to_message_id=message.id,
            message_thread_id=message.message_thread_id,
            quote=True,
        )
        return
    group_settings = await get_chat_config(chat_id=chat.id)
    if group_settings is None:
        settings = {'timer': 3600, 'poll_timeout': 0}
        await set_chat_config(chat_id=chat.id, settings=settings)
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    'Quiz Repeat: 1H',
                    callback_data=f'grp_rpt_{chat.id}_{user.id}')
            ],
            [
                InlineKeyboardButton(
                    'Poll Timeout: Off',
                    callback_data=f'grp_tmt_{chat.id}_{user.id}')
            ],
            [
                InlineKeyboardButton(
                    'Select Categories',
                    callback_data=f'grp_cat_{chat.id}_{user.id}')
            ],
            [
                InlineKeyboardButton(
                    'Reset Quiz State',
                    callback_data=f'grp_rst_{chat.id}_{user.id}')
            ],
            [
                InlineKeyboardButton(
                    'Close Settings',
                    callback_data=f'grp_cnl_{chat.id}_{user.id}')
            ],
        ])
    else:
        timeout_mapping = {
            900: '15m',
            1800: '30m',
            2700: '45m',
            3600: '1H',
            5400: '1.5H',
            7200: '2H'
        }
        poll_timeout_mapping = {
            0: 'Off',
            60: '1m',
            120: '2m',
            300: '5m',
            600: '10m'
        }
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f'Quiz Repeat: {timeout_mapping.get(group_settings.get("timer"))}',
                    callback_data=f'grp_rpt_{chat.id}_{user.id}')
            ],
            [
                InlineKeyboardButton(
                    f'Poll Timeout: {poll_timeout_mapping.get(group_settings.get("poll_timeout"))}',
                    callback_data=f'grp_tmt_{chat.id}_{user.id}')
            ],
            [
                InlineKeyboardButton(
                    'Select Categories',
                    callback_data=f'grp_cat_{chat.id}_{user.id}')
            ],
            [
                InlineKeyboardButton(
                    'Reset Quiz State',
                    callback_data=f'grp_rst_{chat.id}_{user.id}')
            ],
            [
                InlineKeyboardButton(
                    'Close Settings',
                    callback_data=f'grp_cnl_{chat.id}_{user.id}')
            ],
        ])
    await message.reply_text(
        text="Click the buttons below to change the group settings:",
        reply_to_message_id=message.id,
        quote=True,
        reply_markup=keyboard)
