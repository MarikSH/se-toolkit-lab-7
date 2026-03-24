# Bot development plan

In this lab I will build a Telegram bot with a clean, testable architecture. The main goal of Task 1 is to scaffold the project so that command handlers can be tested without a real Telegram connection. I will keep all Telegram‑specific code in bot.py and put the command logic into separate handler functions. This will make it easy to call the same logic both from the --test mode and from the real Telegram bot later.

First, I will create the bot/ directory with bot.py, handlers/, services/, config.py, pyproject.toml, and this PLAN.md file. The config module will be responsible for loading environment variables from .env.bot.secret, including BOT_TOKEN, LMS_API_URL, LMS_API_KEY, and LLM settings. In Task 1 I will only need this configuration for future use, but having it early will simplify the next tasks.

Then I will implement basic handlers for /start, /help, /health, and unknown commands. Each handler will be a pure function that takes input data and returns a string response. The --test mode in bot.py will parse the command from the command line and route it to the appropriate handler. For now, handlers can return simple placeholder text.

Finally, I will add a minimal pyproject.toml and use uv sync to install dependencies. After that I will verify that uv run bot.py --test "/start" and the other test commands work and do not crash. In later tasks I will extend the services layer with HTTP clients for the LMS backend and an LLM client, add more intents, and then wire the same handlers to the real Telegram updates.
mkdir -p bot/handlers bot/services
