import io
from datetime import datetime, timedelta
from io import BytesIO
from typing import Final, Tuple

import matplotlib.pyplot as plt
import pytz
from sqlalchemy import Text, cast, create_engine, desc, func
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import sessionmaker
from telegram.ext import ContextTypes

from bot.database.models import (ActiveGroupStat, ActiveUserStat, PollAnswer,
                                 UserPreferences, UserScore, WeeklyScore)
from bot.helpers.yaml import load_config

# YAML Loader
db_config = load_config("config.yml")["database"]

# Constants
DB_SCHEMA: Final[str] = db_config.get("schema")

db_engine = create_engine(DB_SCHEMA)
Session = sessionmaker(bind=db_engine)


async def get_top_scores(chat_id: int):
    try:
        session = Session()
        top_scores = (session.query(
            UserScore.user_id,
            UserScore.score).filter_by(chat_id=chat_id).join(
                UserPreferences,
                UserScore.user_id == UserPreferences.user_id,
                isouter=True).filter(
                    UserPreferences.settings.is_(None)
                    | (cast(UserPreferences.settings, Text)).contains("off")).
                      filter(UserScore.score > 0).order_by(
                          desc(UserScore.score)).all())
        session.close()
        return top_scores
    except Exception as e:
        print(f"Error fetching top scores: {e}")
        return []


async def get_top_weekly_scores(chat_id: int):
    try:
        session = Session()
        top_weekly_scores = (session.query(
            WeeklyScore.user_id,
            WeeklyScore.score).filter_by(chat_id=chat_id).join(
                UserPreferences,
                WeeklyScore.user_id == UserPreferences.user_id,
                isouter=True).filter(
                    UserPreferences.settings.is_(None)
                    | (cast(UserPreferences.settings, Text)).contains("off")).
                             filter(WeeklyScore.score > 0).order_by(
                                 desc(WeeklyScore.score)).all())
        session.close()
        return top_weekly_scores
    except Exception as e:
        print(f"Error fetching top weekly scores: {e}")
        return []


async def reset_weekly_scores(context: ContextTypes.DEFAULT_TYPE) -> None:
    session = Session()
    try:
        session.query(WeeklyScore).update({
            WeeklyScore.score: 0,
            WeeklyScore.correct_answers: 0,
            WeeklyScore.wrong_answers: 0
        })
        session.commit()
        session.close()
    except Exception as e:
        print(f"Error resetting weekly scores: {e}")


async def get_user_score(chat_id: int, user_id: int):
    session = Session()
    try:
        user_score_record = (session.query(
            UserScore.score, UserScore.correct_answers,
            UserScore.wrong_answers).filter_by(chat_id=chat_id,
                                               user_id=user_id).first())
        session.close()
        if user_score_record:
            user_score, correct_answers, wrong_answers = user_score_record
            accuracy = (correct_answers / (correct_answers + wrong_answers)
                        ) * 100 if correct_answers + wrong_answers > 0 else 0
            return (user_score, correct_answers, wrong_answers, accuracy)
        else:
            return (0, 0, 0, 0)
    except Exception as ex:
        print(f'Error fetching user scores: {ex}')
        return (None, None, None, None)


async def get_user_total_score(user_id: int):
    session = Session()
    try:
        total_score, total_correct_answers, total_wrong_answers = (
            session.query(
                func.coalesce(func.sum(UserScore.score), 0),
                func.coalesce(func.sum(UserScore.correct_answers), 0),
                func.coalesce(func.sum(UserScore.wrong_answers),
                              0)).filter_by(user_id=user_id).first())
        session.close()
        return (total_score, total_correct_answers, total_wrong_answers)
    except Exception as ex:
        print(f'Error fetching user\'s total scores: {ex}')
        return (None, None, None)


async def get_poll_answer_record(poll_id: str):
    session = Session()
    try:
        poll_answer_record = session.query(
            PollAnswer.chat_id,
            PollAnswer.correct_option_id).filter_by(poll_id=poll_id).first()
        session.close()
        return poll_answer_record
    except Exception as e:
        print(f"Error in get_poll_answer_record function: {e}")
        return None


async def update_user_scores(user_id: int, poll_id: str, option_id: int):
    session = Session()
    poll_answer_record = await get_poll_answer_record(poll_id=poll_id)
    if poll_answer_record:
        chat_id, correct_option_id = poll_answer_record
        try:
            if correct_option_id == option_id:
                user_score = session.query(UserScore).filter_by(
                    user_id=user_id, chat_id=chat_id).first()
                weekly_score = session.query(WeeklyScore).filter_by(
                    user_id=user_id, chat_id=chat_id).first()
                if user_score:
                    user_score.score += 1
                    user_score.correct_answers += 1
                else:
                    user_score = UserScore(user_id=user_id,
                                           chat_id=chat_id,
                                           score=1,
                                           correct_answers=1)
                    session.add(user_score)
                if weekly_score:
                    weekly_score.score += 1
                    weekly_score.correct_answers += 1
                else:
                    weekly_score = WeeklyScore(user_id=user_id,
                                               chat_id=chat_id,
                                               score=1,
                                               correct_answers=1)
                    session.add(weekly_score)
            else:
                user_score = session.query(UserScore).filter_by(
                    user_id=user_id, chat_id=chat_id).first()
                weekly_score = session.query(WeeklyScore).filter_by(
                    user_id=user_id, chat_id=chat_id).first()
                if user_score:
                    user_score.score -= 0.5
                    user_score.wrong_answers += 1
                else:
                    user_score = UserScore(user_id=user_id,
                                           chat_id=chat_id,
                                           score=-0.5,
                                           wrong_answers=1)
                    session.add(user_score)
                if weekly_score:
                    weekly_score.score -= 0.5
                    weekly_score.wrong_answers += 1
                else:
                    weekly_score = WeeklyScore(user_id=user_id,
                                               chat_id=chat_id,
                                               score=-0.5,
                                               wrong_answers=1)
                    session.add(weekly_score)
            session.commit()
            session.close()
        except Exception as e:
            print(f"Error in update_user_scores function: {e}")


async def update_user_stat(user_id: int) -> None:
    session = Session()
    current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    try:
        record = session.query(ActiveUserStat).filter_by(user_id=user_id).one()
        record.last_quiz_active_time = current_time
    except NoResultFound:
        new_record = ActiveUserStat(user_id=user_id,
                                    last_quiz_active_time=current_time)
        session.add(new_record)
    session.commit()


async def update_chat_stat(chat_id: int) -> None:
    session = Session()
    current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    try:
        record = session.query(ActiveGroupStat).filter_by(
            chat_id=chat_id).one()
        record.last_quiz_group_active_time = current_time
    except NoResultFound:
        new_record = ActiveGroupStat(chat_id=chat_id,
                                     last_quiz_group_active_time=current_time)
        session.add(new_record)
    session.commit()


async def delete_old_user_stats(context: ContextTypes.DEFAULT_TYPE) -> None:
    session = Session()
    current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    threshold_time = current_time - timedelta(hours=24)
    session.query(ActiveUserStat).filter(
        ActiveUserStat.last_quiz_active_time < threshold_time).delete()
    session.commit()


async def delete_old_chat_stats(context: ContextTypes.DEFAULT_TYPE) -> None:
    session = Session()
    current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    threshold_time = current_time - timedelta(hours=24)
    session.query(ActiveGroupStat).filter(
        ActiveGroupStat.last_quiz_group_active_time < threshold_time).delete()
    session.commit()


def create_answers_distribution_plot(total_correct_answers: int,
                                     total_wrong_answers: int,
                                     total_score: float,
                                     dark_mode=False) -> Tuple[str, BytesIO]:
    if dark_mode:
        background_color = 'black'
        text_color = 'white'
        correct_color = '#006400'
        wrong_color = '#8B0000'
    else:
        background_color = 'white'
        text_color = 'black'
        correct_color = 'lightgreen'
        wrong_color = 'lightcoral'

    total_accuracy = (
        total_correct_answers / (total_correct_answers + total_wrong_answers)
    ) * 100 if total_correct_answers + total_wrong_answers > 0 else 0
    labels = ['Correct Answers', 'Wrong Answers']
    values = [total_correct_answers, total_wrong_answers]
    fig, ax = plt.subplots()
    fig.patch.set_facecolor(background_color)
    ax.set_facecolor(background_color)
    ax.bar(labels, values, color=[correct_color, wrong_color], width=0.5)
    ax.set_xlabel('Category', color=text_color)
    ax.set_ylabel('Count', color=text_color)
    ax.set_title('Total Answers Distribution', color=text_color)
    for i, value in enumerate(values):
        ax.text(i,
                value,
                str(value),
                ha='center',
                va='bottom',
                color=text_color)
    ax.spines['bottom'].set_color(text_color)
    ax.spines['top'].set_color(text_color)
    ax.spines['right'].set_color(text_color)
    ax.spines['left'].set_color(text_color)
    ax.tick_params(axis='x', colors=text_color)
    ax.tick_params(axis='y', colors=text_color)
    legend_labels = ['Correct Answers', 'Wrong Answers']
    legend_colors = [
        plt.Rectangle((0, 0), 1, 1, color=color)
        for color in [correct_color, wrong_color]
    ]
    legend = ax.legend(legend_colors, legend_labels)
    legend.get_frame().set_facecolor(background_color)
    for text in legend.get_texts():
        text.set_color(text_color)
    caption = f"Total Score Across Chats: {total_score}\nAccuracy: {total_accuracy:.2f}%"
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', facecolor=background_color)
    buffer.seek(0)
    return caption, buffer
