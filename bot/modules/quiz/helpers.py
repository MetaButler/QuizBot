from telegram.ext import ContextTypes
from telegram import Poll
from bot.modules.quiz.services import Session, get_random_opentdb_category, get_random_trivia_category
import html
import random
from bot.modules.quiz.services import insert_question_into_db, is_question_sent
from bot.helpers.http import fetch_question, process_opentdb_api_data, process_trivia_api_data

async def process_question_from_opentdb(context: ContextTypes.DEFAULT_TYPE, chat_id: int, data: dict, message_thread_id: int):
    if 'results' not in data or not data['results']:
        return
    question_data = await process_opentdb_api_data(data)
    poll_id = await context.bot.send_poll(
        chat_id=chat_id,
        question=question_data['question'],
        options=question_data['options'],
        correct_option_id=question_data['correct_option_id'],
        message_thread_id=message_thread_id,
        is_anonymous=False,
        type=Poll.QUIZ
    )
    if poll_id:
        insert_question_into_db(chat_id, question_data['question_id'], question_data['correct_option_id'])

async def process_question_from_trivia_api(context: ContextTypes.DEFAULT_TYPE, chat_id: int, data: list, message_thread_id: int):
    if not data or not isinstance(data, list):
        return
    question_data = await process_trivia_api_data(data)
    poll_id = await context.bot.send_poll(
        chat_id=chat_id,
        question=question_data['question'],
        options=question_data['options'],
        correct_option_id=question_data['correct_option_id'],
        message_thread_id=message_thread_id,
        is_anonymous=False,
        type=Poll.QUIZ
    )
    if poll_id:
        insert_question_into_db(chat_id, question_data['question_id'], question_data['correct_option_id'])

async def auto(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_thread_id):
    session = Session()
    try:
        total_retries = 0
        max_retries = 3
        while total_retries < 2 * max_retries:
            use_trivia_api = random.choice([True, False])
            if use_trivia_api:
                if total_retries // 2 < max_retries:
                    category = get_random_trivia_category(session, chat_id)
                    data = fetch_question(category, True)
                    if data and isinstance(data, list) and data:
                        selected_question = random.choice(data)
                        question_id = selected_question['id']
                        if not is_question_sent(session, chat_id, question_id):
                            process_question_from_trivia_api(context, chat_id, data, message_thread_id)
                            return
                    else:
                        print("Failed to fetch a question from Trivia API")
                else:
                    print("Exceeded Trivia API retry limit")
            else:
                if total_retries // 2 < max_retries:
                    category = get_random_opentdb_category(session, chat_id)
                    data = fetch_question(category, False)
                    if data and 'results' in data and data['results']:
                        question_id = data['results'][0]['question']
                        if not is_question_sent(session, chat_id, question_id):
                            process_question_from_opentdb(context, chat_id, data, message_thread_id)
                            return
                    else:
                        print("Failed to fetch a question from OpenTDB")
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