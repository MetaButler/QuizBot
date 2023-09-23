import psycopg2
import matplotlib.pyplot as plt
import numpy as np
import io
from prettytable import PrettyTable
from telegram import Update
from telegram.ext import CallbackContext
import configparser
from .database import create_tables

config = configparser.ConfigParser()
config.read('config.ini')

DATABASE_URL = config['database']['DATABASE_URL']

def log_user_response(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = user.id
    poll_id = update.poll_answer.poll_id
    option_id = update.poll_answer.option_ids[0]

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute('SELECT chat_id, correct_option_id FROM poll_answers WHERE poll_id = %s', (poll_id,))
    row = cursor.fetchone()

    if row:
        chat_id, correct_option_id = row
        if correct_option_id == option_id:
            cursor.execute('INSERT INTO user_scores (user_id, chat_id, score, correct_answers) VALUES (%s, %s, 1, 1) ON CONFLICT (user_id, chat_id) DO UPDATE SET score = user_scores.score + 1, correct_answers = user_scores.correct_answers + 1',
                           (user_id, chat_id))
            cursor.execute('INSERT INTO weekly_scores (user_id, chat_id, score, correct_answers) VALUES (%s, %s, 1, 1) ON CONFLICT (user_id, chat_id) DO UPDATE SET score = weekly_scores.score + 1, correct_answers = weekly_scores.correct_answers + 1',
                           (user_id, chat_id))
        else:
            cursor.execute('INSERT INTO user_scores (user_id, chat_id, score, wrong_answers) VALUES (%s, %s, -0.5, 1) ON CONFLICT (user_id, chat_id) DO UPDATE SET score = user_scores.score - 0.5, wrong_answers = user_scores.wrong_answers + 1',
                           (user_id, chat_id))
            cursor.execute('INSERT INTO weekly_scores (user_id, chat_id, score, wrong_answers) VALUES (%s, %s, -0.5, 1) ON CONFLICT (user_id, chat_id) DO UPDATE SET score = weekly_scores.score - 0.5, wrong_answers = weekly_scores.wrong_answers + 1',
                           (user_id, chat_id))

        conn.commit()

    conn.close()


def get_top_scores(chat_id, limit=5):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_id, score
        FROM user_scores
        WHERE chat_id = %s
        ORDER BY score DESC
        LIMIT %s
    ''', (chat_id, limit))

    top_scores = cursor.fetchall()

    conn.close()

    return top_scores

def rank(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    top_scores = get_top_scores(chat_id)

    if not top_scores:
        update.message.reply_text("No scores found for this chat.")
        return

    message = "Top Score Holders:\n"
    for i, (user_id, score) in enumerate(top_scores, start=1):
        user = context.bot.get_chat_member(chat_id, user_id).user
        if i == 1:
            trophy = "🏆"
        elif i == 2:
            trophy = "🥈"
        elif i == 3:
            trophy = "🥉" 
        else:
            trophy = "🏅"
        
        username = f"{user.first_name}: {score}".ljust(20)
        message += f"{trophy}{username}\n"

    update.message.reply_text(message)

def weekly_rank(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    top_weekly_scores = get_top_weekly_scores(chat_id)

    if not top_weekly_scores:
        update.message.reply_text("No weekly scores found for this chat.")
        return

    message = "Weekly Score Holders:\n"
    for i, (user_id, score) in enumerate(top_weekly_scores, start=1):
        user = context.bot.get_chat_member(chat_id, user_id).user
        if i == 1:
            trophy = "🏆"
        elif i == 2:
            trophy = "🥈"
        elif i == 3:
            trophy = "🥉"
        else:
            trophy = "🏅"

        username = f"{user.first_name}: {score:.2f}".ljust(20)
        message += f"{trophy}{username}\n"

    update.message.reply_text(message)

def get_top_weekly_scores(chat_id, limit=5):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT user_id, score
        FROM weekly_scores
        WHERE chat_id = %s
        ORDER BY score DESC
        LIMIT %s
    ''', (chat_id, limit))

    top_weekly_scores = cursor.fetchall()

    conn.close()

    return top_weekly_scores

def score(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id
    userid = str(user.id)
    user_id = f"{' ' * (10 - len(userid))}{userid}" if len(userid) < 10 else userid[:10]
    username = user.first_name[:15]
    user_name = f"{username}{' ' * (15 - len(username))}" if len(username) < 15 else username[:15]
    
    conn = psycopg2.connect(DATABASE_URL)
    create_tables(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT score, correct_answers, wrong_answers FROM user_scores WHERE chat_id = %s AND user_id = %s", (chat_id, user_id))
    row = cursor.fetchone()

    if row:
        user_score, correct_answers, wrong_answers = row
        accuracy = (correct_answers / (correct_answers + wrong_answers)) * 100 if correct_answers + wrong_answers > 0 else 0

        table = PrettyTable()
        table.field_names = [user_name, user_id]
        table.align[user_name] = "l"
        table.align[user_id] = "r"
        table.add_row(["Your Score", f"{user_score:.2f}"])
        table.add_row(["Correct Answers", str(correct_answers)])
        table.add_row(["Wrong Answers", str(wrong_answers)])
        table.add_row(["Accuracy", f"{accuracy:.2f}%"])

        table_str = table.get_string()

        update.message.reply_text(f"```\n{table_str}\n```", parse_mode="Markdown")
    else:
        update.message.reply_text("Your Score: Go Answer Some Questions")

    conn.close()

def score_dm_total(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_id = user.id

    conn = psycopg2.connect(DATABASE_URL)
    create_tables(conn)
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(score), SUM(correct_answers), SUM(wrong_answers) FROM user_scores WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()

    conn.close()

    if row:
        total_score, total_correct_answers, total_wrong_answers = row
        total_accuracy = (total_correct_answers / (total_correct_answers + total_wrong_answers)) * 100 if total_correct_answers + total_wrong_answers > 0 else 0

        labels = ['Correct Answers', 'Wrong Answers']
        values = [total_correct_answers, total_wrong_answers]
        x = np.arange(len(labels))
        width = 0.35

        fig, ax = plt.subplots()
        rects = ax.bar(x, values, width, label='Count')

        ax.set_xlabel('Category')
        ax.set_ylabel('Count')
        ax.set_title('Total Answers Distribution')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()

        for rect in rects:
            height = rect.get_height()
            ax.annotate(f'{height}',
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')

        caption = f"Total Score Across Chats: {total_score}\nAccuracy: {total_accuracy:.2f}%"

        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)

        update.message.reply_photo(photo=io.BufferedReader(buffer), caption=caption)

        plt.close()
    else:
        update.message.reply_text("Your Total Score: 0")

def reset_weekly_scores():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE weekly_scores "
        "SET score = 0, correct_answers = 0, wrong_answers = 0"
    )

    conn.commit()
    conn.close()