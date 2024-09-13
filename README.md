# 🌟 QuizBot: A Fun and Engaging Quiz Experience for Telegram Groups 🌟

<p align="center">
  <img src="path-to-your-logo.png" alt="QuizBot Logo" width="200"/>
</p>

---

## 📖 Overview

**QuizBot** is a feature-rich Telegram bot designed to provide engaging quiz experiences for your Telegram groups. Powered by the [OpenTDB](https://opentdb.com/) and [The Open Trivia API](https://the-trivia-api.com/), this bot automates quiz deliveries, tracks scores, and provides insightful statistics with a beautiful and modular codebase.

---

## ✨ Features

1. **Quiz Integration**: Connects to [The OpenTDB](https://opentdb.com/) and [The Open Trivia API](https://the-trivia-api.com/) to fetch quiz categories and questions.
2. **Automated Quiz Delivery**: Sends quizzes to subscribed groups at configurable intervals: 15m, 30m, 45m, 1H, 1.5H, or 2H.
3. **Admin Settings**: Group admins have access to intuitive settings via Inline Buttons for easy quiz management.
4. **Score Tracking and Graphs**: Displays ranks, scores, weekly scores, and generates stunning score graphs.
5. **Bot Statistics**:
   - Total number of chats the bot has joined.
   - Total number of users who have interacted with the bot.
   - Number of chats with answered quizzes in the last 24H.
   - Number of users who answered a quiz in the last 24H.
6. **Modular Architecture**: Designed for easy extensibility, allowing new features to be added seamlessly.
7. **Docker Support**: Out-of-the-box support for Docker and Docker Compose for quick setup and deployment.

---

## 🚀 Getting Started

Follow the instructions below to get your instance of **QuizBot** up and running.

### Step 1: Set Up Environment Variables

1. **Option A**: Copy the `.env.sample` file to `.env` and replace the placeholder values with your secure values for username, password, and DB name:

   ```bash
   cp .env.sample .env
   ```

   Update the values in the `.env` file.

2. **Option B**: Directly modify the `docker-compose.yml` file and hardcode the database credentials:

   ```yaml
   POSTGRES_USER: yourusername
   POSTGRES_PASSWORD: yourpassword
   POSTGRES_DB: yourdbname
   ```

### Step 2: Configure Bot Settings

1. Copy `sample_config.yml` to `config.yml`:

   ```bash
   cp sample_config.yml config.yml
   ```

2. Update the `config.yml` file:
   - Set the `telegram.bot_token` and other necessary settings.
   - Ensure the `database.schema` matches the credentials from Step 1.

### Step 3: Configure Alembic

1. Copy `sample_alembic.ini` to `alembic.ini`:

   ```bash
   cp sample_alembic.ini alembic.ini
   ```

2. Edit the `sqlalchemy.url` in `alembic.ini` to match the `database.schema` from Step 2.

### Step 4: Build and Run the Bot

1. Pull the necessary database image, build the bot image, and start the bot:

   ```bash
   docker compose up --build --detach
   ```

2. To stop the bot, run:

   ```bash
   docker compose down
   ```

---

## 💾 Example Database Schemas

Here are two valid SQLAlchemy schemas for easy setup:

- PostgreSQL:  
  `postgresql://dbbotuser:EU39RVEE7hFkh5Dr85Hsq6YYzaQ2AQxf@postgres:5432/quizbotdb`

- SQLite:  
  `sqlite:///quizbot.db`

---

## 🛠 Primary Dependencies

The **QuizBot** project relies on the following key libraries:

```toml
python-telegram-bot = {extras = ["all"], version = "==21.5"}
matplotlib = "==3.9.2"
pyyaml = "==6.0.2"
sqlalchemy = "==2.0.34"
pytz = "==2024.2"
alembic = "==1.13.2"
psycopg2-binary = "*"
```

Make sure to refer to the [official documentation](https://docs.python-telegram-bot.org/) of `python-telegram-bot` for more detailed information about the library's capabilities.

---

## 📊 Stats & Performance

With its built-in analytics, **QuizBot** can track:

- Number of chats the bot has been added to.
- Total users who have interacted with the bot.
- Chats where quizzes have been answered in the past 24 hours.
- Users who answered a quiz in the past 24 hours.

The bot's ability to generate beautiful graphs enhances the quiz experience by providing visual representations of score progressions.

---

## 🧩 Extensibility

Thanks to its **modular design**, adding new features to **QuizBot** is straightforward. Developers can easily integrate new functionality without disrupting the core bot.

If you're interested in contributing to this project, feel free to submit a pull request or open an issue on the [GitHub repository](https://github.com/MetaButler/QuizBot).

---

## 🐋 Docker Support

**QuizBot** is fully compatible with Docker, making deployment and management effortless. You can easily start the bot using Docker Compose, and it supports both PostgreSQL and SQLite databases out of the box.

- [Learn more about Docker](https://www.docker.com/get-started)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

## 🤝 Contributing

We welcome contributions! Please check out our [contribution guidelines](https://github.com/MetaButler/QuizBot/blob/main/CONTRIBUTING.md) for more information on how to get started.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/MetaButler/QuizBot/blob/main/LICENSE) file for details.

---

<p align="center">
  Made with ❤️ by the Atlas Projects Team
</p>
