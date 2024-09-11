from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from bot.helpers.yaml import load_config
from typing import Final, List
import re

# YAML Loader
broadcast_config = load_config("config.yml")["broadcast"]
telegram_config = load_config("config.yml")["telegram"]

# Constants
AUTHORIZED_IDS: Final[List[int]] = [
    int(telegram_id) for telegram_id in telegram_config["authorized_ids"]
]


async def broadcast(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if user.id not in AUTHORIZED_IDS:
        await message.reply_text(
            text="You are not authorized to use this command!",
            reply_to_message_id=message.id,
            quote=True)
        return
    if len(message.text.split(maxsplit=1)) == 1:
        await message.reply_text(
            text="You need to provide some text to broadcast",
            reply_to_message_id=message.id,
            quote=True)
        return
    message_as_markdown = message.text_markdown_v2.split(maxsplit=1)[1]
    buttonurl_pattern = r"buttonurl:\s\\\[(.*)\\\]\s{1}(\\{\\{\w+\\}\\}|https:\/\/\S+)"
    buttonurl_matches = re.findall(buttonurl_pattern, message_as_markdown)
    for buttonurl_match in buttonurl_matches:
        message_as_markdown = message_as_markdown.replace(
            f'buttonurl: \\[{buttonurl_match[0]}\\] {str(buttonurl_match[1]).encode("raw_unicode_escape").decode("unicode_escape")}',
            "")
    button_urls = list()
    button_texts = list()
    for i in range(len(buttonurl_matches)):
        button_urls.append(
            str(buttonurl_matches[i][-1]).encode('raw_unicode_escape').decode(
                'unicode_escape'))
        button_texts.append(
            str(buttonurl_matches[i][0]).encode('raw_unicode_escape').decode(
                'unicode_escape'))
        button_urls[i] = str(button_urls[i]).replace('\\', '')
        if str(button_urls[i]).startswith("{{") and str(
                button_urls[i]).replace("{{", "").replace(
                    "}}", "") in broadcast_config.keys():
            button_urls[i] = broadcast_config[str(button_urls[i]).replace(
                "{{", "").replace("}}", "")]
    for match in button_urls:
        if str(match).startswith("{{"):
            await message.reply_text(
                text=f"Missing {str(match)} in config",
                reply_to_message_id=message.id,
                quote=True,
            )
            return
    keyboard = list()
    for url, text in zip(button_urls, button_texts):
        keyboard.append([InlineKeyboardButton(text=text, url=url)])
    await message.reply_text(
        text=
        f"This is how your broadcast will look like:\n\n{message_as_markdown.strip()}",
        reply_to_message_id=message.id,
        quote=True,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    await _.bot.send_message(
        chat_id=chat.id,
        text="Do you want to proceed?",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton('Yes ✅',
                                 callback_data=rf'brdcst_yes_{user.id}'),
            InlineKeyboardButton('No ❌', callback_data=rf'brdcst_no_{user.id}')
        ]]))
