from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.modules.scores.services import get_top_scores, get_top_weekly_scores, get_user_score, get_user_total_score
import matplotlib.pyplot as plt
import io

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

async def score(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    user_score, correct_answers, wrong_answers, accuracy = await get_user_score(chat_id=chat.id, user_id=user.id)
    if all(var is None for var in [user_score, correct_answers, wrong_answers, accuracy]):
        await message.reply_text(
            text='Some error occurred, please retry later',
            quote=True,
            allow_sending_without_reply=True,
            reply_to_message_id=message.id
        )
        return
    elif all(var == 0 for var in [user_score, correct_answers, wrong_answers, accuracy]):
        await message.reply_text(
            text='Go answer some questions first to get a score!',
            quote=True,
            allow_sending_without_reply=True,
            reply_to_message_id=message.id
        )
        return
    else:
        message_text = "Your Score:"
        await message.reply_text(
            text=message_text,
            allow_sending_without_reply=True,
            quote=True,
            reply_to_message_id=message.id,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text=f"{user.full_name}", callback_data='score_btn'),
                        InlineKeyboardButton(text=f"{user.id}", callback_data='score_btn'),
                    ],
                    [
                        InlineKeyboardButton(text="Your Score", callback_data='score_btn'),
                        InlineKeyboardButton(text=f"{user_score}", callback_data='score_btn'),
                    ],
                    [
                        InlineKeyboardButton(text="Correct Answers", callback_data='score_btn'),
                        InlineKeyboardButton(text=f"{correct_answers}", callback_data='score_btn'),
                    ],
                    [
                        InlineKeyboardButton(text="Wrong Answers", callback_data='score_btn'),
                        InlineKeyboardButton(text=f"{wrong_answers}", callback_data='score_btn'),
                    ],
                    [
                        InlineKeyboardButton(text="Accuracy", callback_data='score_btn'),
                        InlineKeyboardButton(text=f"{accuracy}", callback_data='score_btn'),
                    ],
                ]
            )
        )

async def scores_dm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user

    total_score, total_correct_answers, total_wrong_answers = await get_user_total_score(user_id=user.id)
    if all(var is None for var in [total_score, total_correct_answers, total_wrong_answers]):
        await message.reply_text(
            text='Something went wrong, please retry later',
            quote=True,
            allow_sending_without_reply=True,
            reply_to_message_id=message.id
        )
        return
    elif all(var == 0 for var in [total_score, total_correct_answers, total_wrong_answers]):
        await message.reply_text(
            text='Go answer some questions first to get a score!',
            quote=True,
            allow_sending_without_reply=True,
            reply_to_message_id=message.id
        )
        return
    else:
        total_accuracy = (total_correct_answers / (total_correct_answers + total_wrong_answers)) * 100 if total_correct_answers + total_wrong_answers > 0 else 0
        labels = ['Correct Answers', 'Wrong Answers']
        values = [total_correct_answers, total_wrong_answers]
        fig, ax = plt.subplots()
        ax.bar(labels, values)
        ax.set_xlabel('Category')
        ax.set_ylabel('Count')
        ax.set_title('Total Answers Distribution')
        for i, value in enumerate(values):
            ax.text(i, value, str(value), ha='center', va='bottom')
        caption = f"Total Score Across Chats: {total_score}\nAccuracy: {total_accuracy:.2f}%"
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        await message.reply_photo(
            photo=io.BufferedReader(buffer),
            caption=caption,
            allow_sending_without_reply=True,
            quote=True,
            reply_to_message_id=message.id
        )