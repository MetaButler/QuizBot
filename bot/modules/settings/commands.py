from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.modules.settings.services import get_user_global_config, set_user_global_config

async def settings_dm(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_chat
    message = update.effective_message
    
    user_settings = await get_user_global_config(user_id=user.id)
    if user_settings is None:
        settings = {
            'ui': 'light',
            'privacy': 'on',
        }
        await set_user_global_config(
            user_id=user.id,
            settings=settings,
        )
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(f'UI Color: {settings.get("ui").capitalize()}', callback_data=f'stngs_ui_{user.id}'),],
                [InlineKeyboardButton(f'Privacy: {settings.get("privacy").capitalize()}', callback_data=f'stngs_prvcy_{user.id}')]
            ]
        )
    else:
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(f'UI Color: {user_settings.get("ui").capitalize()}', callback_data=f'stngs_ui_{user.id}'),],
                [InlineKeyboardButton(f'Privacy: {user_settings.get("privacy").capitalize()}', callback_data=f'stngs_prvcy_{user.id}')]
            ]
        )
    await message.reply_text(
        text="Here are your global settings:",
        reply_to_message_id=message.id,
        allow_sending_without_reply=True,
        quote=True,
        reply_markup=keyboard
    )