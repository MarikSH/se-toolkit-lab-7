import sys
from handlers.basic import (
    handle_start,
    handle_help,
    handle_health,
    handle_unknown,
)

def run_test_mode(text: str) -> int:
    text = text.strip()
    if text.startswith("/start"):
        resp = handle_start()
    elif text.startswith("/help"):
        resp = handle_help()
    elif text.startswith("/health"):
        resp = handle_health()
    else:
        resp = handle_unknown(text)
    print(resp)
    return 0

def main() -> None:
    if "--test" in sys.argv:
        try:
            idx = sys.argv.index("--test")
            query = sys.argv[idx + 1]
        except (ValueError, IndexError):
            print('Usage: bot.py --test "/command"')
            sys.exit(1)
        code = run_test_mode(query)
        sys.exit(code)
    else:
        print("Telegram mode is not implemented yet for Task 1.")
        sys.exit(0)

if __name__ == "__main__":
    main()
