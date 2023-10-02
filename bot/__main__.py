from bot.main import application, db_engine
from bot.database.models import Base
from bot.helpers.http import fetch_opentdb_categories, fetch_the_trivia_categories
from bot.helpers.services import insert_categories_into_topics
from typing import Final

OPENTDB_API_URL: Final[str] = "https://opentdb.com/api_category.php"
THE_TRIVIA_API_URL: Final[str] = "https://the-trivia-api.com/v2/categories"

if __name__ == '__main__':
    print("Creating tables inside database now...")
    Base.metadata.create_all(db_engine)

    print("Fetching categories now...")
    opentdb_categories = fetch_opentdb_categories(OPENTDB_API_URL)
    the_trivia_categories = fetch_the_trivia_categories(THE_TRIVIA_API_URL)
    merged_categories = opentdb_categories + the_trivia_categories
    insert_categories_into_topics(merged_categories)

    print("Bot starting...")
    application.run_polling()