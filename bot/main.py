from bot.helpers.yaml import load_config
from bot.modules.misc.commands import start, help, stats
from bot.modules.quiz.commands import enablequiz, disablequiz, quizstatus
from bot.modules.scores.commands import rank, weekly_rank, score, scores_dm
from bot.modules.scores.callbacks import handle_score_button, log_user_response
from typing import Final
from sqlalchemy import create_engine
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, filters, PollAnswerHandler

# YAML Loader
telegram_config = load_config("config.yml")["telegram"]
db_config = load_config("config.yml")["database"]

# Constants
DB_SCHEMA: Final[str] = db_config.get("schema")
BOT_TOKEN: Final[str] = telegram_config.get("bot_token")

# Builders
db_engine = create_engine(DB_SCHEMA)
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Handlers
start_handler = CommandHandler('start', start)
help_handler = CommandHandler('help', help)
enablequiz_handler = CommandHandler('enablequiz', enablequiz)
disablequiz_handler = CommandHandler('disablequiz', disablequiz)
quizstatus_handler = CommandHandler('quizstatus', quizstatus)
stats_handler = CommandHandler('stats', stats)
rank_handler = CommandHandler('rank', rank)
weekly_rank_handler = CommandHandler('week', weekly_rank)
handle_score_button_handler = CallbackQueryHandler(handle_score_button, pattern=r'score_btn')
score_handler = CommandHandler('score', score, (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP))
scores_dm_handler = CommandHandler('score', scores_dm, filters.ChatType.PRIVATE)
poll_answer_handler = PollAnswerHandler(log_user_response)

# Add Handlers
application.add_handler(start_handler)
application.add_handler(help_handler)
application.add_handler(enablequiz_handler)
application.add_handler(disablequiz_handler)
application.add_handler(quizstatus_handler)
application.add_handler(stats_handler)
application.add_handler(rank_handler)
application.add_handler(weekly_rank_handler)
application.add_handler(score_handler)
application.add_handler(scores_dm_handler)
application.add_handler(handle_score_button_handler)
application.add_handler(poll_answer_handler)