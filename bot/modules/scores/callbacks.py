from telegram import Update
from telegram.ext import ContextTypes
from bot.modules.scores.services import update_user_scores

async def handle_score_button(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    This callbackqueryhandler does nothing basically
    Since we will show clickable buttons for scores, we want to answer the CB Queries
    so that Telegram does not bug us later
    """
    await update.callback_query.answer()

async def log_user_response(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    poll_id = update.poll_answer.poll_id
    option_id = update.poll_answer.option_ids[0]
    try:
        await update_user_scores(user_id=user.id, poll_id=poll_id, option_id=option_id)
    except Exception as e:
        print(f"Error in log_user_response function: {e}")