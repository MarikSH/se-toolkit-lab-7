from typing import List

from services.lms import check_health, list_labs, get_pass_rates


def handle_start() -> str:
    return (
        "Welcome to the SE Toolkit bot! "
        "Я бот для работы с LMS: могу показать статус backend'а, список лабораторных и ваши результаты."
    )


def handle_help() -> str:
    return (
        "Доступные команды:\n"
        "/start — приветствие и краткое описание бота\n"
        "/help — список команд и подсказки\n"
        "/health — проверка состояния LMS backend\n"
        "/labs — список лабораторных работ\n"
        "/scores <lab-id> — результаты по задачам для выбранной лабораторной (например, /scores lab-04)"
    )


def handle_health() -> str:
    ok, message = check_health()
    return message


def handle_labs() -> str:
    try:
        labs = list_labs()
    except Exception as exc:
        return f"Backend error while fetching labs: {exc}"

    if not labs:
        return "No labs found in LMS."

    lines: List[str] = ["Available labs:"]
    for lab in labs:
        title = lab.get("title") or lab.get("name") or ""
        lab_code = lab.get("attributes", {}).get("lab_id") or lab.get("code") or ""
        if not lab_code and title.lower().startswith("lab"):
            parts = title.split()
            if len(parts) >= 2 and parts[1].isdigit():
                lab_code = f"lab-{parts[1]}"
        if not lab_code:
            continue
        pretty_id = lab_code.replace("lab-", "Lab ").upper()
        lines.append(f"- {pretty_id} — {title}")
    return "\n".join(lines)


def handle_scores(args: str) -> str:
    lab_id = args.strip()
    if not lab_id:
        return "Usage: /scores <lab-id>, e.g. /scores lab-04"

    try:
        items = get_pass_rates(lab_id)
    except Exception as exc:
        return f"Backend error while fetching scores for {lab_id}: {exc}"

    if not items:
        return f"No scores found for {lab_id}. Check lab id and run ETL sync."

    lines: List[str] = [f"Pass rates for {lab_id.replace('lab-', 'Lab ').upper()}:"]
    for item in items:
        name = item.get("task") or item.get("task_name") or item.get("name") or "Task"
        rate = item.get("avg_score") or item.get("pass_rate") or item.get("percentage") or 0
        attempts = item.get("attempts") or item.get("count") or 0
        try:
            rate_value = float(rate)
            if rate_value <= 1:
                rate_value *= 100.0
        except Exception:
            rate_value = 0.0
        lines.append(f"- {name}: {rate_value:.1f}% ({attempts} attempts)")
    return "\n".join(lines)


def handle_unknown(command: str) -> str:
    return f"Команда '{command}' не поддерживается. Используй /help."
