from telegram import Update
from telegram.ext import ContextTypes

async def handle_score_button(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    This callbackqueryhandler does nothing basically
    Since we will show clickable buttons for scores, we want to answer the CB Queries
    so that Telegram does not bug us later
    """
    await update.callback_query.answer()