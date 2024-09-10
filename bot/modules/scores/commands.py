from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.modules.scores.callbacks import build_scores
from bot.modules.scores.services import get_top_scores, get_top_weekly_scores, get_user_score, get_user_total_score, create_answers_distribution_plot
from bot.modules.settings.services import get_user_global_config
import io
from bot.helpers.misc import get_start_time


async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message

    if int(message.date.timestamp()) < get_start_time():
        return

    if chat.type == 'private':
        await message.reply_text(
            text="This command is not meant to be used in private chats!",
            quote=True,
            reply_to_message_id=message.id)
        return
    top_scores = await get_top_scores(chat_id=chat.id)

    if len(top_scores) == 0:
        await message.reply_text(text="No scores found for this chat!",
                                 quote=True,
                                 reply_to_message_id=message.id)
        return

    text_message = "Top Score Holders:\n"
    score_message = await build_scores(top_scores=top_scores,
                                       context=context,
                                       chat_id=chat.id)
    text_message += score_message

    await message.reply_text(text=text_message,
                             quote=True,
                             reply_to_message_id=message.id)


async def weekly_rank(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message

    if int(message.date.timestamp()) < get_start_time():
        return

    if chat.type == 'private':
        await message.reply_text(
            text="This command is not meant to be used in private chats!",
            quote=True,
            reply_to_message_id=message.id)
        return
    weekly_top_scores = await get_top_weekly_scores(chat_id=chat.id)

    if len(weekly_top_scores) == 0:
        await message.reply_text(text="No scores found for this chat!",
                                 quote=True,
                                 reply_to_message_id=message.id)
        return

    message_text = "Weekly Score Holders:\n"
    score_message = await build_scores(top_scores=weekly_top_scores,
                                       context=context,
                                       chat_id=chat.id)
    message_text += score_message

    await message.reply_text(text=message_text,
                             quote=True,
                             reply_to_message_id=message.id)


async def score(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if int(message.date.timestamp()) < get_start_time():
        return

    user_score, correct_answers, wrong_answers, accuracy = await get_user_score(
        chat_id=chat.id, user_id=user.id)
    if all(var is None
           for var in [user_score, correct_answers, wrong_answers, accuracy]):
        await message.reply_text(
            text='Some error occurred, please retry later',
            quote=True,
            reply_to_message_id=message.id)
        return
    elif all(
            var == 0
            for var in [user_score, correct_answers, wrong_answers, accuracy]):
        await message.reply_text(
            text='Go answer some questions first to get a score!',
            quote=True,
            reply_to_message_id=message.id)
        return
    else:
        message_text = "Your Score:"
        await message.reply_text(
            text=message_text,
            quote=True,
            reply_to_message_id=message.id,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(text=f"{user.full_name}",
                                         callback_data='score_btn'),
                    InlineKeyboardButton(text=f"{user.id}",
                                         callback_data='score_btn'),
                ],
                [
                    InlineKeyboardButton(text="Your Score",
                                         callback_data='score_btn'),
                    InlineKeyboardButton(text=f"{user_score:.2f}",
                                         callback_data='score_btn'),
                ],
                [
                    InlineKeyboardButton(text="Correct Answers",
                                         callback_data='score_btn'),
                    InlineKeyboardButton(text=f"{correct_answers}",
                                         callback_data='score_btn'),
                ],
                [
                    InlineKeyboardButton(text="Wrong Answers",
                                         callback_data='score_btn'),
                    InlineKeyboardButton(text=f"{wrong_answers}",
                                         callback_data='score_btn'),
                ],
                [
                    InlineKeyboardButton(text="Accuracy",
                                         callback_data='score_btn'),
                    InlineKeyboardButton(text=f"{accuracy:.2f}",
                                         callback_data='score_btn'),
                ],
            ]))


async def scores_dm(update: Update,
                    context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    user = update.effective_user

    if int(message.date.timestamp()) < get_start_time():
        return

    total_score, total_correct_answers, total_wrong_answers = await get_user_total_score(
        user_id=user.id)
    if all(var is None for var in
           [total_score, total_correct_answers, total_wrong_answers]):
        await message.reply_text(
            text='Something went wrong, please retry later',
            quote=True,
            reply_to_message_id=message.id)
        return
    elif all(var == 0 for var in
             [total_score, total_correct_answers, total_wrong_answers]):
        await message.reply_text(
            text='Go answer some questions first to get a score!',
            quote=True,
            reply_to_message_id=message.id)
        return
    else:
        user_settings = await get_user_global_config(user_id=user.id)
        if user_settings is not None:
            ui_settings = user_settings.get("ui")
            if ui_settings == 'dark':
                dark_mode = True
            else:
                dark_mode = False
        else:
            dark_mode = False
        caption, buffer = create_answers_distribution_plot(
            total_correct_answers=total_correct_answers,
            total_wrong_answers=total_wrong_answers,
            total_score=total_score,
            dark_mode=dark_mode)
        await message.reply_photo(photo=io.BufferedReader(buffer),
                                  caption=caption,
                                  quote=True,
                                  reply_to_message_id=message.id)
