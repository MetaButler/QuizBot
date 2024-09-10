from typing import Any, List, Tuple

from sqlalchemy import Row
from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from bot.modules.scores.services import (get_poll_answer_record,
                                         update_chat_stat, update_user_scores,
                                         update_user_stat)


async def handle_score_button(update: Update,
                              _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    This callbackqueryhandler does nothing basically
    Since we will show clickable buttons for scores, we want to answer the CB Queries
    so that Telegram does not bug us later
    """
    await update.callback_query.answer()


async def log_user_response(update: Update,
                            _: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    poll_id = update.poll_answer.poll_id
    option_id = update.poll_answer.option_ids[0]
    try:
        await update_user_scores(user_id=user.id,
                                 poll_id=poll_id,
                                 option_id=option_id)
        poll_answer_record = await get_poll_answer_record(poll_id=poll_id)
        if poll_answer_record:
            chat_id, _ = poll_answer_record
        await update_user_stat(user_id=user.id)
        await update_chat_stat(chat_id=chat_id)
    except Exception as e:
        print(f"Error in log_user_response function: {e}")


async def build_scores(top_scores: List[Row[Tuple[int, Any]]] | list,
                       context: ContextTypes.DEFAULT_TYPE,
                       chat_id: int) -> str:
    i = 0
    index = -1
    text_message = ""
    while (index + 1) < len(top_scores):
        index += 1
        user_id, score = top_scores[index]
        try:
            user = await context.bot.get_chat_member(chat_id=chat_id,
                                                     user_id=user_id)
        except BadRequest:
            continue
        i += 1
        if i > 5:
            break

        if i == 1:
            trophy = "🏆"
        elif i == 2:
            trophy = "🥈"
        elif i == 3:
            trophy = "🥉"
        else:
            trophy = "🏅"
        score_message = f'{user.user.full_name}: {score:.2f}'.ljust(20)
        text_message += f'{trophy} {score_message}\n'
    return text_message
