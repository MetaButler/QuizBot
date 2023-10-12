from telegram.ext import ContextTypes
from telegram import Poll
from bot.modules.quiz.services import get_random_opentdb_category, get_random_trivia_category, insert_question_into_db, is_question_sent, set_quiz_false
import random
from bot.helpers.http import fetch_question, process_opentdb_api_data, process_trivia_api_data
from typing import Dict
import asyncio
from telegram.error import Forbidden

async def process_question_from_opentdb(context: ContextTypes.DEFAULT_TYPE, chat_id: int, data: dict, message_thread_id: int, group_settings: Dict[str, int]):
    if 'results' not in data or not data['results']:
        return
    question_data = await process_opentdb_api_data(data)
    try:
        if group_settings is None or (group_settings and int(group_settings["poll_timeout"]) == 0):
            poll_message = await context.bot.send_poll(
                chat_id=chat_id,
                question=question_data['question'],
                options=question_data['options'],
                correct_option_id=question_data['correct_option_id'],
                message_thread_id=message_thread_id,
                is_anonymous=False,
                type=Poll.QUIZ
            )
        else:
            poll_message = await context.bot.send_poll(
                chat_id=chat_id,
                question=question_data['question'],
                options=question_data['options'],
                correct_option_id=question_data['correct_option_id'],
                message_thread_id=message_thread_id,
                is_anonymous=False,
                type=Poll.QUIZ,
                open_period=int(group_settings["poll_timeout"])
            )
        if poll_message:
            await insert_question_into_db(chat_id, question_data['question_id'], question_data['correct_option_id'], poll_message.poll.id)
            await asyncio.sleep(5)
    except Forbidden as fe:
        print(f"Bot was kicked from {chat_id}\nError: {fe}")
        await set_quiz_false(chat_id=chat_id)

async def process_question_from_trivia_api(context: ContextTypes.DEFAULT_TYPE, chat_id: int, data: list, message_thread_id: int, group_settings: Dict[str, int]):
    if not data or not isinstance(data, list):
        return
    question_data = await process_trivia_api_data(data)
    try:
        if group_settings is None or (group_settings and int(group_settings["poll_timeout"]) == 0):
            poll_message = await context.bot.send_poll(
                chat_id=chat_id,
                question=question_data['question'],
                options=question_data['options'],
                correct_option_id=question_data['correct_option_id'],
                message_thread_id=message_thread_id,
                is_anonymous=False,
                type=Poll.QUIZ
            )
        else:
            poll_message = await context.bot.send_poll(
                chat_id=chat_id,
                question=question_data['question'],
                options=question_data['options'],
                correct_option_id=question_data['correct_option_id'],
                message_thread_id=message_thread_id,
                is_anonymous=False,
                type=Poll.QUIZ,
                open_period=int(group_settings["poll_timeout"])
            )
        if poll_message:
            await insert_question_into_db(chat_id, question_data['question_id'], question_data['correct_option_id'], poll_message.poll.id)
            await asyncio.sleep(5)
    except Forbidden as fe:
        print(f'Bot was kicked from chat: {chat_id}\nError: {fe}')
        await set_quiz_false(chat_id=chat_id)

async def auto(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_thread_id: int, group_settings: Dict[str, int]):
    try:
        total_retries = 0
        max_retries = 3
        while total_retries < 2 * max_retries:
            use_trivia_api = True
            opentdb_categories = get_random_opentdb_category(chat_id=chat_id)
            trivia_categories = get_random_opentdb_category(chat_id=chat_id)
            if (opentdb_categories is None and trivia_categories is None) or (opentdb_categories is not None and trivia_categories is not None):
                use_trivia_api = random.choice([True, False])
            else:
                if opentdb_categories is None:
                    use_trivia_api = True
                elif trivia_categories is None:
                    use_trivia_api = False
            if use_trivia_api:
                if total_retries // 2 < max_retries:
                    category = get_random_trivia_category(chat_id)
                    data = await fetch_question(category, True)
                    if data and isinstance(data, list) and data:
                        selected_question = random.choice(data)
                        question_id = selected_question['id']
                        if not is_question_sent(chat_id, question_id):
                            await process_question_from_trivia_api(context, chat_id, data, message_thread_id, group_settings)
                            return
                    else:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="No more questions found. Maybe you should enable more categories!"
                        )
                        print("Failed to fetch a question from Trivia API")
                        return
                else:
                    print("Exceeded Trivia API retry limit")
            else:
                if total_retries // 2 < max_retries:
                    category = get_random_opentdb_category(chat_id)
                    data = await fetch_question(category, False)
                    if data and 'results' in data and data['results']:
                        question_id = data['results'][0]['question']
                        if not is_question_sent(chat_id, question_id):
                            await process_question_from_opentdb(context, chat_id, data, message_thread_id, group_settings)
                            return
                    else:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="No more questions found. Maybe you should enable more categories!"
                        )
                        print("Failed to fetch a question from OpenTDB")
                        return
                else:
                    print("Exceeded OpenTDB retry limit")
            total_retries += 1
        await context.bot.send_message(
            chat_id=chat_id,
            text="Sorry, no new questions were found"
        )
        print("No new question found after retries")
    except Exception as e:
        print(f"An error occurred: {e}")