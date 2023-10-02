import httpx
from typing import List, Dict
import random
import html

def fetch_opentdb_categories(API_URL_OPENTDB: str) -> List[Dict[str, str]]:
    try:
        with httpx.Client() as client:
            response = client.get(API_URL_OPENTDB)
            response.raise_for_status()
            data = response.json()
            categories = []

            for category in data.get("trivia_categories", []):
                categories.append({"category_id": str(category["id"]), "category_name": category["name"], "source": "opentdb"})

            return categories
    except httpx.HTTPError as e:
        print(f"Failed to fetch categories from {API_URL_OPENTDB}: {e}")
        return []

def fetch_the_trivia_categories(API_URL_TRIVIA: str) -> List[Dict[str, str]]:
    try:
        with httpx.Client() as client:
            response = client.get(API_URL_TRIVIA)
            response.raise_for_status()
            data = response.json()
            categories = []

            for category_name, subcategories in data.items():
                if subcategories:
                    category_id = subcategories[0]
                    categories.append({"category_id": category_id, "category_name": category_name, "source": "trivia"})

            return categories
    except httpx.HTTPError as e:
        print(f"Failed to fetch categories from {API_URL_TRIVIA}: {e}")
        return []
    
async def fetch_question(category=None, trivia_api=False):
    base_url = 'https://opentdb.com/api.php' if not trivia_api else 'https://the-trivia-api.com/v2/questions'
    params = dict()
    if trivia_api:
        if category:
            params['categories'] = category
    else:
        params['amount'] = 1
        if category:
            params['category'] = category
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            return data
        except httpx.RequestError as re:
            print(f"Failed to fetch data: {re}")
            return None
        
async def process_trivia_api_data(data):
    selected_question = random.choice(data)
    question_id = selected_question['id']
    question = selected_question.get('question', {}).get('text', "")
    correct_answer = selected_question.get('correctAnswer', "")
    incorrect_answers = [html.unescape(option) for option in selected_question.get('incorrectAnswers', [])]
    options = random.sample(incorrect_answers, min(3, len(incorrect_answers)))
    options.append(correct_answer)
    random.shuffle(options)
    correct_option_id = options.index(correct_answer)
    return {
        "question": question,
        "options": options,
        "correct_option_id": correct_option_id,
        "question_id": question_id,
    }

async def process_opentdb_api_data(data):
    question_id = data['results'][0]['question']
    question = html.unescape(data['results'][0]['question'])
    correct_answer = html.unescape(data['results'][0]['correct_answer'])
    incorrect_answers = [html.unescape(option) for option in data['results'][0]['incorrect_answers']]
    options = random.sample(incorrect_answers, min(3, len(incorrect_answers)))
    options.append(correct_answer)
    random.shuffle(options)
    correct_option_id = options.index(correct_answer)
    return {
        "question": question,
        "options": options,
        "correct_option_id": correct_option_id,
        "question_id": question_id,
    }

async def fetch_quiz_question():
    use_trivia_api = random.choice([True, False])
    data = await fetch_question(None, use_trivia_api)
    if not use_trivia_api and 'results' in data and data['results']:
        quiz_data = await process_opentdb_api_data(data)
    elif use_trivia_api and data and isinstance(data, list):
        quiz_data = await process_trivia_api_data(data)
    if not quiz_data:
        print("No quiz questions found from the API.")
        return None
    return quiz_data