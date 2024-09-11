from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.modules.categories.services import fetch_category_names, get_chat_ids_in_group_preferences, determine_source, update_database, reset_topics_to_none, fetch_categories

group_button_states = dict()


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    chat_id = query.message.chat_id
    category_id = query.data
    query_data_unpacked = query.data.split(
        '#') if '#' in query.data else query.data.split('_')
    if int(query_data_unpacked[-1]) != query.from_user.id:
        await query.answer(text="This button is not meant for you",
                           show_alert=True)
        return
    await query.answer("Please wait while we process...")
    if not category_id.startswith(
        ("clear_", "next_page_", "prev_page_", "done_", "reset_", "close_")):
        category_id = category_id.split('#')[1]
        if chat_id in group_button_states:
            if category_id in group_button_states[chat_id]:
                group_button_states[chat_id].pop(category_id)
            else:
                group_button_states[chat_id][category_id] = True
    if category_id.startswith("clear_"):
        context.user_data.pop('trivia_topics', None)
        context.user_data.pop('opentdb_topics', None)
        group_button_states.pop(chat_id, None)
        category_names = fetch_category_names()
        keyboard = await paginate_category_names(category_names,
                                                 page=1,
                                                 chat_id=query.message.chat_id,
                                                 user_id=query.from_user.id)
        await query.edit_message_text(
            text=
            "You can control your categories by pressing the buttons below:",
            reply_markup=keyboard,
        )
        await query.answer("Selection cleared.")
    elif category_id.startswith(("next_page_", "prev_page_")):
        await handle_page_navigation(update, context, category_id)
    elif category_id.startswith("done_"):
        await done(update, context)
    elif category_id.startswith("reset_"):
        await reset(update, context)
    elif category_id.startswith("close_"):
        await query.edit_message_text(text="Cancelled category selection")
        return
    else:
        category_data = fetch_category_names()
        category_name = category_data.get(category_id)
        selected_source = determine_source(category_id)
        if selected_source is None:
            await query.answer("Failed to determine source.")
            return
        if selected_source == 'opentdb':
            opentdb_topics = context.user_data.get('opentdb_topics', '')
            opentdb_topics_split = str(opentdb_topics).split(',')
            if category_id in opentdb_topics_split:
                opentdb_topics_split.remove(category_id)
            else:
                opentdb_topics_split.append(category_id)
            opentdb_topics = ",".join(opentdb_topics_split)
            context.user_data['opentdb_topics'] = opentdb_topics
        elif selected_source == 'trivia':
            trivia_topics = context.user_data.get('trivia_topics', '')
            trivia_topics_split = str(trivia_topics).split(',')
            if category_id in trivia_topics_split:
                trivia_topics_split.remove(category_id)
            else:
                trivia_topics_split.append(category_id)
            trivia_topics = ",".join(trivia_topics_split)
            context.user_data['trivia_topics'] = trivia_topics
        updated_category_name = "✅ " + category_name
        keyboard = []
        for row in query.message.reply_markup.inline_keyboard:
            row_keyboard = []
            for button in row:
                if '#' in button.callback_data:
                    check_category_id = button.callback_data.split('#')[1]
                else:
                    check_category_id = None
                if check_category_id is None or check_category_id != category_id:
                    row_keyboard.append(button)
                else:
                    if button.text.startswith("✅ "):
                        row_keyboard.append(
                            InlineKeyboardButton(
                                text=f'{category_name}',
                                callback_data=button.callback_data))
                    else:
                        row_keyboard.append(
                            InlineKeyboardButton(
                                text=f'{updated_category_name}',
                                callback_data=button.callback_data))
            keyboard.append(row_keyboard)
        await query.edit_message_text(
            text=
            "You can control your categories by pressing the buttons below:",
            reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_page_navigation(update: Update,
                                 context: ContextTypes.DEFAULT_TYPE,
                                 action: str) -> None:
    query = update.callback_query
    chat_id = query.message.chat_id
    current_page = context.user_data.get('page', 1)
    if action.startswith("next_page_"):
        current_page += 1
    elif action.startswith("prev_page_"):
        current_page = max(current_page - 1, 1)
    context.user_data['page'] = current_page
    category_names = fetch_category_names()
    if not category_names:
        await query.answer("Failed to fetch category names.")
        return
    keyboard = await paginate_category_names(category_names,
                                             page=current_page,
                                             chat_id=chat_id,
                                             user_id=query.from_user.id)
    await query.edit_message_text(
        text="You can control your categories by pressing the buttons below:",
        reply_markup=keyboard)


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.edit_message_text(text="Selection completed, saving to DB...")
    update_database(query.message.chat_id,
                    context.user_data.get('trivia_topics', ''),
                    context.user_data.get('opentdb_topics', ''))
    context.user_data.pop('trivia_topics', None)
    context.user_data.pop('opentdb_topics', None)


async def reset(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.edit_message_text(
        text="Do you really want to reset your group's categories?",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                text='Yes ❌',
                callback_data=f'cat_rst_yes_{query.from_user.id}'),
            InlineKeyboardButton(
                text='No ✅', callback_data=f'cat_rst_no_{query.from_user.id}')
        ]]))


async def handle_reset_btn(update: Update,
                           context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user = query.from_user
    query_data_unpacked = query.data.split('_')
    if int(query_data_unpacked[-1]) != user.id:
        await query.answer(text="This button is not meant for you",
                           show_alert=True)
        return
    await query.answer("Please wait while we process...")
    if query_data_unpacked[2] == 'no':
        await query.edit_message_text(text="Taking no action")
        return
    elif query_data_unpacked[2] == 'yes':
        reset_topics_to_none(query.message.chat_id)
        await query.edit_message_text(
            text="Successfully reset quiz categories for this chat")


async def paginate_category_names(category_data,
                                  page: int,
                                  chat_id: int,
                                  user_id: int,
                                  page_size=10,
                                  first_time=False,
                                  context: ContextTypes.DEFAULT_TYPE = None):
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_names = list(category_data.values())[start_idx:end_idx]
    paginated_ids = list(category_data.keys())[start_idx:end_idx]
    existing_topics = fetch_categories(chat_id=chat_id)
    if existing_topics[0] and existing_topics[1]:
        trivia_topics = set(existing_topics[0].split(',') if (
            existing_topics[0] or not len(existing_topics[0]) == 0) else [])
        opentdb_topics = set(existing_topics[1].split(',') if (
            existing_topics[1] or not len(existing_topics[0]) == 0) else [])
    else:
        trivia_topics = set()
        opentdb_topics = set()
    keyboard = []
    if first_time:
        if existing_topics[0]:
            context.user_data['trivia_topics'] = existing_topics[0]
        if existing_topics[1]:
            context.user_data['opentdb_topics'] = existing_topics[1]
    for i in range(0, len(paginated_names), 2):
        row = []
        for j in range(i, min(i + 2, len(paginated_names))):
            name = paginated_names[j]
            id = paginated_ids[j]
            marked = "✅ " if (
                chat_id in group_button_states
                and id in group_button_states[chat_id]
            ) or id in trivia_topics or id in opentdb_topics else ""
            button = InlineKeyboardButton(
                text=f"{marked}{name}", callback_data=f'topic#{id}#{user_id}')
            row.append(button)
        keyboard.append(row)
    control_row = []
    if page > 1:
        control_row.append(
            InlineKeyboardButton(text="Previous Page",
                                 callback_data=f"prev_page_{user_id}"))
    if end_idx < len(category_data.keys()):
        control_row.append(
            InlineKeyboardButton(text="Next Page",
                                 callback_data=f"next_page_{user_id}"))
    ext_control_row = [
        InlineKeyboardButton(text="Clear", callback_data=f"clear_{user_id}"),
        InlineKeyboardButton(text="Done", callback_data=f"done_{user_id}"),
    ]
    keyboard.append(control_row)
    keyboard.append(ext_control_row)
    keyboard.append([
        InlineKeyboardButton(text="Reset", callback_data=f"reset_{user_id}"),
        InlineKeyboardButton(text="Close", callback_data=f"close_{user_id}"),
    ])
    return InlineKeyboardMarkup(keyboard)


async def handle_category_btn(update: Update,
                              context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    query_data = update.callback_query.data
    user = update.callback_query.from_user
    query_data_unpacked = query_data.split('_')
    if int(query_data_unpacked[-1]) != user.id:
        await query.answer(text="This button is not meant for you",
                           show_alert=True)
        return
    await query.answer("Please wait while we are processing...")
    category_data = fetch_category_names()
    if category_data is None:
        await query.edit_message_text(text="Failed to fetch category names")
        return
    if int(query_data_unpacked[-2]) not in get_chat_ids_in_group_preferences():
        await query.edit_message_text(
            text=
            "To configure categories, enable quiz using the /enablequiz command."
        )
        return
    context.user_data['page'] = 1
    keyboard = await paginate_category_names(category_data=category_data,
                                             page=1,
                                             chat_id=int(
                                                 query_data_unpacked[2]),
                                             user_id=user.id,
                                             first_time=True,
                                             context=context)
    await query.edit_message_text(
        text="You can control your categories by pressing the buttons below:",
        reply_markup=keyboard)
