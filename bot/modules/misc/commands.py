from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_type = update.message.chat.type
    if chat_type == 'private':
        await update.message.reply_text(
            text="Hi, I'm alive! To get a quiz, press: /quiz\n\nIf you want to use this bot in a group for auto quizzes, you can add me to your group by clicking the button below.",
            reply_to_message_id=update.message.id,
            quote=True,
            allow_sending_without_reply=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Add to group", url=f"https://t.me/{context.bot.username}?startgroup=start")]
                ]
            )
        )
    else:
        raise NotImplementedError