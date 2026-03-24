import json
import sys
from typing import Any, Dict, List

from services.llm_client import call_llm_with_tools
from services.tools import TOOLS
from services import lms


SYSTEM_PROMPT = (
    "You are an assistant for the SE Toolkit LMS. "
    "You MUST use the provided tools to answer questions about labs, scores, learners, and analytics. "
    "Do not make up data: always call a tool when you need real information."
)


def _tool_result_message(tool_call_id: str, name: str, result: Any) -> Dict[str, Any]:
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": name,
        "content": json.dumps(result),
    }


def route_nl(user_text: str) -> str:
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]

    # первый вызов — выбираем tools
    msg = call_llm_with_tools(messages, TOOLS)
    tool_calls = msg.get("tool_calls") or []

    if not tool_calls:
        return msg.get("content") or "I could not understand your question."

    tool_results_messages: List[Dict[str, Any]] = []

    for tc in tool_calls:
        func = tc["function"]
        name = func["name"]
        args_str = func.get("arguments") or "{}"
        try:
            args = json.loads(args_str)
        except json.JSONDecodeError:
            args = {}
        print(f"[tool] LLM called: {name}({args})", file=sys.stderr)

        try:
            if name == "get_items":
                result = lms.list_labs()
            elif name == "get_learners":
                result = lms.get_learners()
            elif name == "get_scores":
                result = lms.get_scores(args.get("lab", ""))
            elif name == "get_pass_rates":
                result = lms.get_pass_rates(args.get("lab", ""))
            elif name == "get_timeline":
                result = lms.get_timeline(args.get("lab", ""))
            elif name == "get_groups":
                result = lms.get_groups(args.get("lab", ""))
            elif name == "get_top_learners":
                result = lms.get_top_learners(
                    args.get("lab", ""), int(args.get("limit", 5))
                )
            elif name == "get_completion_rate":
                result = lms.get_completion_rate(args.get("lab", ""))
            elif name == "trigger_sync":
                result = lms.trigger_sync()
            else:
                result = {"error": f"Unknown tool: {name}"}
        except Exception as exc:
            result = {"error": str(exc)}

        print(f"[tool] Result for {name}: {str(result)[:120]}", file=sys.stderr)
        tool_results_messages.append(
            _tool_result_message(tc["id"], name, result)
        )

    # второй вызов — просим LLM сформировать ответ; если он падает, не рушим бота
    messages.append(msg)
    messages.extend(tool_results_messages)
    print(
        f"[summary] Feeding {len(tool_results_messages)} tool results back to LLM",
        file=sys.stderr,
    )
    try:
        final_msg = call_llm_with_tools(messages, TOOLS)
        return final_msg.get("content") or "No answer from LLM."
    except Exception as exc:
        return f"LLM error while summarizing tool results: {exc}"
