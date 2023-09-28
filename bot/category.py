import random
import html
import requests
import psycopg2
from telegram import Update, Poll, Chat, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

import logging
import configparser
from .database import create_tables
config = configparser.ConfigParser()
config.read('config.ini')

DATABASE_URL = config['database']['DATABASE_URL']

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def fetch_category_names():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("SELECT category_name FROM topics")
        category_names = [row[0] for row in cursor.fetchall()]

        return category_names
    except psycopg2.Error as e:
        logging.error(f"Error fetching category names: {e}")
        return []

def get_chat_ids_in_group_preferences():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("SELECT chat_id FROM group_preferences")
        chat_ids = [row[0] for row in cursor.fetchall()]

        return chat_ids
    except psycopg2.Error as e:
        logging.error(f"Error fetching chat_ids in group preferences: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def paginate_category_names(category_names, page, chat_id, page_size=10):
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_names = category_names[start_idx:end_idx]

    keyboard = []

    for i in range(0, len(paginated_names), 2):
        row = []
        for j in range(i, min(i + 2, len(paginated_names))):
            name = paginated_names[j]

            # Check whether this button should be marked
            if chat_id in group_button_states and name in group_button_states[chat_id]:
                name = "✅ " + name

            button = InlineKeyboardButton(text=name, callback_data=name)
            row.append(button)
        keyboard.append(row)

    control_row = []
    if page > 1:
        prev_button = InlineKeyboardButton(text="Previous Page", callback_data="prev_page")
        control_row.append(prev_button)

    if end_idx < len(category_names):
        next_button = InlineKeyboardButton(text="Next Page", callback_data="next_page")
        control_row.append(next_button)

    clear_button = InlineKeyboardButton(text="Clear", callback_data="clear")
    done_button = InlineKeyboardButton(text="Done", callback_data="done")

    control_row.extend([clear_button, done_button])
    keyboard.append(control_row)

    return keyboard


def topics(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id

    category_names = fetch_category_names()

    if not category_names:
        update.message.reply_text("Failed to fetch category names.")
        return

    if chat_id not in get_chat_ids_in_group_preferences():
        update.message.reply_text("To use the quiz feature, please first enable it using the /enablequiz command.")
        return

    context.user_data['page'] = 1

    keyboard = paginate_category_names(category_names, page=1, chat_id=chat_id)

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Select a category:", reply_markup=reply_markup)

group_button_states = {}

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    chat_id = query.message.chat_id
    category_name = query.data

    # When a button is clicked, save its state
    if category_name not in ["clear", "next_page", "prev_page", "done"]:
        if chat_id not in group_button_states:
            group_button_states[chat_id] = {}
        group_button_states[chat_id][category_name] = True

    if category_name == "clear":
        context.user_data.pop('trivia_topics', None)
        context.user_data.pop('opentdb_topics', None)
        update_database(chat_id, None, None)

        # Clear the tick boxes for this chat immediately
        if chat_id in group_button_states:
            del group_button_states[chat_id]

        # Regenerate the category buttons with cleared tick boxes
        category_names = fetch_category_names()
        keyboard = paginate_category_names(category_names, page=1, chat_id=chat_id)

        query.edit_message_text(text="Select a category:", reply_markup=InlineKeyboardMarkup(keyboard))

        query.answer("Selection cleared.")
    elif category_name == "next_page":
        next_page(update, context)
    elif category_name == "prev_page":
        prev_page(update, context)
    elif category_name == "done":
        done(update, context)
    else:
        selected_source = determine_source(category_name)

        if selected_source is None:
            query.answer("Failed to determine source.")
            return

        category_id = fetch_category_id(category_name, selected_source)

        if category_id is not None:
            if selected_source == 'trivia':
                trivia_topics = context.user_data.get('trivia_topics', '')
                if trivia_topics:
                    trivia_topics += ","
                trivia_topics += str(category_id)
                context.user_data['trivia_topics'] = trivia_topics
            elif selected_source == 'opentdb':
                opentdb_topics = context.user_data.get('opentdb_topics', '')
                if opentdb_topics:
                    opentdb_topics += ","
                opentdb_topics += str(category_id)
                context.user_data['opentdb_topics'] = opentdb_topics

            update_database(chat_id, context.user_data.get('trivia_topics', ''), context.user_data.get('opentdb_topics', ''))

            updated_category_name = "✅ " + category_name

            for row in query.message.reply_markup.inline_keyboard:
                for button in row:
                    if button.callback_data == category_name:
                        button.text = updated_category_name
                        break

            query.edit_message_text("Select a category:", reply_markup=query.message.reply_markup)

            query.answer(f"You selected: {category_name}")
        else:
            query.answer("Failed to fetch category_id.")



def done(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    chat_id = query.message.chat_id

    message = query.message.reply_text("Selection complete. You can now proceed.", reply_markup=InlineKeyboardMarkup([]))

    context.bot.delete_message(chat_id=chat_id, message_id=query.message.message_id)

    context.user_data['done_message'] = message.message_id

def prev_page(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    if query.message:
        chat_id = query.message.chat_id
        current_page = context.user_data.get('page', 1)

        current_page -= 1 if current_page > 1 else 0

        context.user_data['page'] = current_page

        category_names = fetch_category_names()

        if not category_names:
            query.answer("Failed to fetch category names.")
            return

        keyboard = paginate_category_names(category_names, page=current_page, chat_id=chat_id)

        query.edit_message_text(text="Select a category:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        query.answer("Failed to navigate to the previous page. Please start over.")



def determine_source(category_name):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("SELECT source FROM topics WHERE category_name = %s", (category_name,))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return None
    except psycopg2.Error as e:
        logging.error(f"Error determining source: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def fetch_category_id(category_name, selected_source):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("SELECT category_id FROM topics WHERE category_name = %s AND source = %s",
                       (category_name, selected_source))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            return None
    except psycopg2.Error as e:
        logging.error(f"Error fetching category_id: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_database(chat_id, trivia_topics, opentdb_topics):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("SELECT trivia_topics, opentdb_topics FROM group_preferences WHERE chat_id = %s", (chat_id,))
        result = cursor.fetchone()
        existing_trivia_topics, existing_opentdb_topics = result if result else (None, None)

        if trivia_topics:
            if existing_trivia_topics:
                trivia_topics = ",".join(set(existing_trivia_topics.split(",") + trivia_topics.split(",")))
        if opentdb_topics:
            if existing_opentdb_topics:
                opentdb_topics = ",".join(set(existing_opentdb_topics.split(",") + opentdb_topics.split(",")))

        cursor.execute("UPDATE group_preferences SET trivia_topics = %s, opentdb_topics = %s WHERE chat_id = %s",
                       (trivia_topics, opentdb_topics, chat_id))

        conn.commit()
    except psycopg2.Error as e:
        logging.error(f"Error updating database: {e}")
    finally:
        cursor.close()
        conn.close()


def next_page(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    if query.message:
        chat_id = query.message.chat_id
        current_page = context.user_data.get('page', 1)

        current_page += 1

        context.user_data['page'] = current_page

        category_names = fetch_category_names()

        if not category_names:
            query.answer("Failed to fetch category names.")
            return

        keyboard = paginate_category_names(category_names, page=current_page, chat_id=chat_id)

        query.edit_message_text(text="Select a category:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        query.answer("Failed to navigate to the next page. Please start over.")