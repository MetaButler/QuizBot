from telegram import Update
from telegram.ext import ContextTypes
from bot.modules.scores.services import get_top_scores, get_top_weekly_scores

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message

    if chat.type == 'private':
        await message.reply_text(
            text="This command is not meant to be used in private chats!",
            allow_sending_without_reply=True,
            quote=True,
            reply_to_message_id=message.id
        )
        return
    top_scores = await get_top_scores(chat_id=chat.id)
    
    if len(top_scores) == 0:
        await message.reply_text(
            text="No scores found for this chat!",
            allow_sending_without_reply=True,
            quote=True,
            reply_to_message_id=message.id
        )
        return
    
    text_message = "Top Score Holders:\n"
    for i, (user_id, score) in enumerate(top_scores, start=1):
        user = await context.bot.get_chat_member(
            chat_id=chat.id,
            user_id=user_id
        )
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
    
    await message.reply_text(
        text=text_message,
        allow_sending_without_reply=True,
        quote=True,
        reply_to_message_id=message.id
    )

async def weekly_rank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message

    if chat.type == 'private':
        await message.reply_text(
            text="This command is not meant to be used in private chats!",
            allow_sending_without_reply=True,
            quote=True,
            reply_to_message_id=message.id
        )
        return
    weekly_top_scores = await get_top_weekly_scores(chat_id=chat.id)

    if len(weekly_top_scores) == 0:
        await message.reply_text(
            text="No scores found for this chat!",
            allow_sending_without_reply=True,
            quote=True,
            reply_to_message_id=message.id
        )
        return
    
    message_text = "Weekly Score Holders:\n"
    for i, (user_id, score) in enumerate(weekly_top_scores, start=1):
        user = await context.bot.get_chat_member(
            chat_id=chat.id,
            user_id=user_id
        )
        if i == 1:
            trophy = "🏆"
        elif i == 2:
            trophy = "🥈"
        elif i == 3:
            trophy = "🥉"
        else:
            trophy = "🏅"

        score_message = f"{user.user.full_name}: {score:.2f}".ljust(20)
        message_text += f"{trophy} {score_message}\n"

    await message.reply_text(
        text=message_text,
        allow_sending_without_reply=True,
        quote=True,
        reply_to_message_id=message.id
    )