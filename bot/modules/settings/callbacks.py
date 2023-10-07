from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.modules.settings.services import get_user_global_config, set_user_global_config

async def user_global_settings(update: Update, _: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    query_data = update.callback_query.data
    user = update.callback_query.from_user
    query_data_unpacked = query_data.split('_')
    if int(query_data_unpacked[2]) != user.id:
        await query.answer(
            text="This button is not meant for you",
            show_alert=True
        )
        return
    await query.answer("Please wait while we are processing...")
    user_settings = await get_user_global_config(user.id)
    if query_data_unpacked[1] == 'ui':
        ui_data = user_settings.get("ui")
        if ui_data == 'light':
            await set_user_global_config(
                user_id=user.id,
                settings={
                    'ui': 'dark',
                    'privacy': user_settings.get("privacy"),
                }
            )
            ui_color = 'dark'
        else:
            await set_user_global_config(
                user_id=user.id,
                settings={
                    'ui': 'light',
                    'privacy': user_settings.get("privacy"),
                }
            )
            ui_color = 'light'
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(f'UI Color: {ui_color.capitalize()}', callback_data=f'stngs_ui_{user.id}')],
                    [InlineKeyboardButton(f'Privacy: {user_settings.get("privacy").capitalize()}', callback_data=f'stngs_prvcy_{user.id}')]
                ]
            )
        )
    else:
        # query_type is prvcy
        privacy_data = user_settings.get("privacy")
        if privacy_data == 'on':
            await set_user_global_config(
                user_id=user.id,
                settings={
                    'ui': user_settings.get("ui"),
                    'privacy': 'off',
                }
            )
            privacy = 'off'
        else:
            await set_user_global_config(
                user_id=user.id,
                settings={
                    'ui': user_settings.get("ui"),
                    'privacy': 'on',
                }
            )
            privacy = 'on'
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(f'UI Color: {user_settings.get("ui").capitalize()}', callback_data=f'stngs_ui_{user.id}')],
                    [InlineKeyboardButton(f'Privacy: {privacy.capitalize()}', callback_data=f'stngs_prvcy_{user.id}')]
                ]
            )
        )