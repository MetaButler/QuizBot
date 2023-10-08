from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.modules.settings.services import get_user_global_config, set_user_global_config, get_chat_config, set_chat_config, reset_chat_questions

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

async def chat_settings(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.callback_query.from_user
    query_data = query.data
    query_data_unpacked = query_data.split('_')
    if int(query_data_unpacked[3]) != user.id:
        await query.answer(
            text='This button is not meant for you',
            show_alert=True
        )
        return
    await query.answer('Please wait while we are processing...')
    group_settings = await get_chat_config(chat_id=int(query_data_unpacked[2]))
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
    if query_data_unpacked[1] == 'rpt':
        db_timeout = int(group_settings.get('timer'))
        timeout_list = sorted(timeout_mapping.keys())
        db_timeout_index = timeout_list.index(db_timeout)
        new_timeout_list = timeout_list[db_timeout_index + 1:] + timeout_list[:db_timeout_index] + [db_timeout]
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [
                [InlineKeyboardButton(f'Quiz Repeat: {timeout_mapping.get(new_timeout_list[0])}', callback_data=f'grp_rpt_{int(query_data_unpacked[2])}_{user.id}')],
                [InlineKeyboardButton(f'Poll Timeout: {poll_timeout_mapping.get(group_settings.get("poll_timeout"))}', callback_data=f'grp_tmt_{int(query_data_unpacked[2])}_{user.id}')],
                [InlineKeyboardButton('Select Categories', callback_data=f'grp_cat_{int(query_data_unpacked[2])}_{user.id}')],
                [InlineKeyboardButton('Reset Quiz State', callback_data=f'grp_rst_{int(query_data_unpacked[2])}_{user.id}')],
                [InlineKeyboardButton('Close Settings', callback_data=f'grp_cnl_{int(query_data_unpacked[2])}_{user.id}')],
                ]
            )
        )
        await set_chat_config(
            chat_id=int(query_data_unpacked[2]),
            settings={
                'timer': new_timeout_list[0],
                'poll_timeout': group_settings.get("poll_timeout"),
            }
        )
    elif query_data_unpacked[1] == 'tmt':
        db_poll_timeout = int(group_settings.get('poll_timeout'))
        poll_timeout_list = sorted(poll_timeout_mapping.keys())
        poll_timeout_index = poll_timeout_list.index(db_poll_timeout)
        new_poll_timeout_list = poll_timeout_list[poll_timeout_index + 1:] + poll_timeout_list[:poll_timeout_index] + [db_poll_timeout]
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(f'Quiz Repeat: {timeout_mapping.get(group_settings.get("timer"))}', callback_data=f'grp_rpt_{int(query_data_unpacked[2])}_{user.id}')],
                    [InlineKeyboardButton(f'Poll Timeout: {poll_timeout_mapping.get(new_poll_timeout_list[0])}', callback_data=f'grp_tmt_{int(query_data_unpacked[2])}_{user.id}')],
                    [InlineKeyboardButton('Select Categories', callback_data=f'grp_cat_{int(query_data_unpacked[2])}_{user.id}')],
                    [InlineKeyboardButton('Reset Quiz State', callback_data=f'grp_rst_{int(query_data_unpacked[2])}_{user.id}')],
                    [InlineKeyboardButton('Close Settings', callback_data=f'grp_cnl_{int(query_data_unpacked[2])}_{user.id}')],
                ]
            )
        )
        await set_chat_config(
            chat_id=int(query_data_unpacked[2]),
            settings={
                'timer': group_settings.get("timer"),
                'poll_timeout': new_poll_timeout_list[0],
            }
        )
    elif query_data_unpacked[1] == 'cat':
        raise NotImplementedError
    elif query_data_unpacked[1] == 'rst':
        await query.edit_message_text(
            text="Do you really want to reset chat questions?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton('Yes ❌', callback_data=f'rst_yes_{int(query_data_unpacked[2])}_{user.id}')],
                    [InlineKeyboardButton('No ✅', callback_data=f'rst_no_{int(query_data_unpacked[2])}_{user.id}')],
                ]
            )
        )

async def reset_chat_questions_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.callback_query.from_user
    query_data = query.data
    query_data_unpacked = query_data.split('_')
    if int(query_data_unpacked[3]) != user.id:
        await query.answer(
            text='This button is not meant for you',
            show_alert=True
        )
        return
    await query.answer('Please wait while we are processing...')
    if query_data_unpacked[1] == 'yes':
        delete_result = await reset_chat_questions(chat_id=int(query_data_unpacked[2]))
        if delete_result is None:
            await query.edit_message_text(
                text="Failed to reset chat questions, retry later"
            )
            return
        else:
            if delete_result:
                await query.edit_message_text(
                    text="Successfully cleared chat questions!"
                )
                return
            else:
                await query.edit_message_text(
                    text="There was no questions to clear"
                )
                return
    elif query_data_unpacked[1] == 'no':
        await query.edit_message_text(
            text="Taking no action"
        )
        return
    
async def close_settings_btn(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = update.callback_query.from_user
    query_data = query.data
    query_data_unpacked = query_data.split('_')
    if int(query_data_unpacked[3]) != user.id:
        await query.answer(
            text='This button is not meant for you',
            show_alert=True
        )
        return
    await query.answer('Please wait while we are processing...')
    await query.edit_message_text(
        text='Settings Closed!'
    )