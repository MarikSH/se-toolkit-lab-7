def handle_start() -> str:
    return "Привет! Я бот курса SE Toolkit. Напиши /help, чтобы увидеть доступные команды."

def handle_help() -> str:
    return "Доступные команды: /start, /help, /health. Остальные пока не реализованы."

def handle_health() -> str:
    return "Backend health: OK (stub for Task 1)."

def handle_unknown(command: str) -> str:
    return f"Команда '{command}' не поддерживается. Используй /help."
