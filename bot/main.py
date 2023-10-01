from bot.helpers.yaml import load_config
from bot.modules.misc.commands import start, help
from bot.modules.quiz.commands import enablequiz, disablequiz, quizstatus
from typing import Final, List
from sqlalchemy import create_engine
from telegram.ext import ApplicationBuilder, CommandHandler

# YAML Loader
telegram_config = load_config("config.yml")["telegram"]
db_config = load_config("config.yml")["database"]

# Constants
DB_SCHEMA: Final[str] = db_config.get("schema")
BOT_TOKEN: Final[str] = telegram_config.get("bot_token")
AUTHORIZED_IDS: Final[List[int]] = [int(telegram_id) for telegram_id in telegram_config["authorized_ids"]]

# Builders
db_engine = create_engine(DB_SCHEMA)
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Handlers
start_handler = CommandHandler('start', start)
help_handler = CommandHandler('help', help)
enablequiz_handler = CommandHandler('enablequiz', enablequiz)
disablequiz_handler = CommandHandler('disablequiz', disablequiz)
quizstatus_handler = CommandHandler('quizstatus', quizstatus)

# Add Handlers
application.add_handler(start_handler)
application.add_handler(help_handler)
application.add_handler(enablequiz_handler)
application.add_handler(disablequiz_handler)
application.add_handler(quizstatus_handler)