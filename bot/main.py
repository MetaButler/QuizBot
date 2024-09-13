from datetime import datetime
from typing import Final

import pytz
from sqlalchemy import create_engine
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler,
                          CommandHandler, PollAnswerHandler, filters)

from bot.helpers.yaml import load_config
from bot.modules.categories.callbacks import (button, handle_category_btn,
                                              handle_reset_btn)
from bot.modules.misc.commands import help, start, stats
from bot.modules.quiz.callbacks import send_auto_question_with_timeout
from bot.modules.quiz.commands import disablequiz, enablequiz, quiz, quizstatus
from bot.modules.scores.callbacks import handle_score_button, log_user_response
from bot.modules.scores.commands import rank, score, scores_dm, weekly_rank
from bot.modules.scores.services import (delete_old_chat_stats,
                                         delete_old_user_stats,
                                         reset_weekly_scores)
from bot.modules.settings.callbacks import (chat_settings, close_settings_btn,
                                            reset_chat_questions_handler,
                                            user_global_settings)
from bot.modules.settings.commands import settings, settings_dm

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
handle_score_button_handler = CallbackQueryHandler(handle_score_button,
                                                   pattern=r'score_btn')
score_handler = CommandHandler(
    'score', score, (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP))
scores_dm_handler = CommandHandler('score', scores_dm,
                                   filters.ChatType.PRIVATE)
quiz_handler = CommandHandler('quiz', quiz)
poll_answer_handler = PollAnswerHandler(log_user_response)
settings_dm_handler = CommandHandler('settings', settings_dm,
                                     filters.ChatType.PRIVATE)
settings_dm_cb_handler = CallbackQueryHandler(
    user_global_settings, pattern=r'^stngs_(ui|prvcy)_\d+$')
settings_handler = CommandHandler(
    'settings', settings,
    (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP))
settings_grp_cb_handler = CallbackQueryHandler(
    chat_settings, pattern=r'^grp_(rpt|tmt|rst)_-\d+_\d+$')
reset_chat_qstns_cb_handler = CallbackQueryHandler(
    reset_chat_questions_handler, pattern=r'^rst_(yes|no)_-\d+_\d+$')
close_settings_btn_handler = CallbackQueryHandler(
    close_settings_btn, pattern=r'^grp_cnl_-\d+_\d+$')
handle_category_btn_handler = CallbackQueryHandler(
    handle_category_btn, pattern=r'^grp_cat_-\d+_\d+$')
clear_button_handler = CallbackQueryHandler(button, r'^clear_\d+$')
navi_page_button_handler = CallbackQueryHandler(button,
                                                r'^(next|prev)_page_\d+$')
done_page_button_handler = CallbackQueryHandler(button, r'^done_\d+$')
reset_cat_button_handler = CallbackQueryHandler(button, r'^reset_\d+$')
topic_button_handler = CallbackQueryHandler(button, r'^topic#.*$')
close_page_button_handler = CallbackQueryHandler(button, r'^close_\d+$')
category_reset_btn = CallbackQueryHandler(handle_reset_btn,
                                          pattern=r'^cat_rst_(yes|no)_\d+$')

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
application.add_handler(quiz_handler)
application.add_handler(poll_answer_handler)
application.add_handler(settings_dm_handler)
application.add_handler(settings_dm_cb_handler)
application.add_handler(settings_handler)
application.add_handler(settings_grp_cb_handler)
application.add_handler(reset_chat_qstns_cb_handler)
application.add_handler(close_settings_btn_handler)
application.add_handler(handle_category_btn_handler)
application.add_handler(clear_button_handler)
application.add_handler(navi_page_button_handler)
application.add_handler(done_page_button_handler)
application.add_handler(reset_cat_button_handler)
application.add_handler(topic_button_handler)
application.add_handler(category_reset_btn)
application.add_handler(close_page_button_handler)

# Job Queueing
job_queue = application.job_queue
time_midnight = datetime.now(pytz.timezone('Asia/Kolkata')).replace(
    hour=1, minute=0, second=0, microsecond=0)
job_queue.run_daily(
    callback=reset_weekly_scores,
    days=(0, ),
    time=time_midnight,
)
job_queue.run_repeating(
    callback=send_auto_question_with_timeout,
    data=900,
    interval=900,
    first=10,
)
job_queue.run_repeating(
    callback=send_auto_question_with_timeout,
    data=1800,
    interval=1800,
    first=10,
)
job_queue.run_repeating(
    callback=send_auto_question_with_timeout,
    data=2700,
    interval=2700,
    first=10,
)
job_queue.run_repeating(
    callback=send_auto_question_with_timeout,
    data=3600,
    interval=3600,
    first=10,
)
job_queue.run_repeating(
    callback=send_auto_question_with_timeout,
    data=5400,
    interval=5400,
    first=10,
)
job_queue.run_repeating(
    callback=send_auto_question_with_timeout,
    data=7200,
    interval=7200,
    first=10,
)
job_queue.run_repeating(
    callback=delete_old_user_stats,
    interval=60,
    first=10,
)
job_queue.run_repeating(
    callback=delete_old_chat_stats,
    interval=60,
    first=10,
)
