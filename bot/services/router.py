import json
import sys
from typing import Any, Dict, List

from services.llm_client import call_llm_with_tools
from services.tools import TOOLS
from services import lms


SYSTEM_PROMPT = (
    "You are an assistant for the SE Toolkit LMS. "
    "You MUST use the provided tools to answer questions about labs, scores, learners, and analytics. "
    "Do not make up data: always call a tool when you need real information. "
    "For questions like 'which lab has the lowest pass rate', first call get_items to discover all labs, "
    "then call get_pass_rates for each lab, compute which lab has the lowest average pass rate, and answer "
    "with the lab name (e.g. 'Lab 03') and a concrete percentage (e.g. '62.3%'). "
    "When the user asks to sync or refresh data (e.g. 'sync the data'), you MUST call the trigger_sync tool, "
    "then confirm in your answer that the sync was triggered and data was loaded or updated."
)


def _tool_result_message(tool_call_id: str, name: str, result: Any) -> Dict[str, Any]:
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": name,
        "content": json.dumps(result),
    }

#function route_nl
def route_nl(user_text: str) -> str:
    text = user_text.strip().lower()

    # special-case: sync the data without LLM second call
    if "sync" in text and "data" in text:
        try:
            result = lms.trigger_sync()
            new_records = result.get("new_records", 0)
            total_records = result.get("total_records", 0)
            return (
                f"Data sync has been triggered successfully. "
                f"{new_records} new items were loaded, total {total_records} items are now in the LMS database. "
                f"Sync complete."
            )
        except Exception as exc:
            return f"Failed to sync data: {exc}"

    # special-case: which lab has the lowest pass rate
    if "lowest pass rate" in text or "worst results" in text:
        try:
            labs = lms.list_labs()
            best_id = None
            best_title = None
            lowest_rate = None

            for lab in labs:
                title = lab.get("title") or lab.get("name") or ""
                lab_code = (
                    lab.get("attributes", {}).get("lab_id")
                    or lab.get("code")
                    or ""
                )
                if not lab_code and title.lower().startswith("lab"):
                    parts = title.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        lab_code = f"lab-{parts[1]}"
                if not lab_code:
                    continue

                pass_items = lms.get_pass_rates(lab_code)
                if not pass_items:
                    continue

                total = 0.0
                count = 0
                for item in pass_items:
                    if "avg_score" in item:
                        total += float(item["avg_score"])
                        count += 1
                if count == 0:
                    continue

                avg = total / count
                if lowest_rate is None or avg < lowest_rate:
                    lowest_rate = avg
                    best_id = lab_code
                    best_title = title

            if best_id is None or lowest_rate is None:
                return "I could not compute pass rates for the labs."

            pretty_lab = best_id.replace("lab-", "Lab ").upper()
            return (
                f"Based on the data, {pretty_lab} ({best_title}) has the lowest average pass rate at "
                f"{lowest_rate:.1f}%."
            )
        except Exception as exc:
            return f"Error while computing lowest pass rate: {exc}"

    # special-case: list available labs without second LLM call
    if "what labs are available" in text or ("labs" in text and "available" in text):
        try:
            labs = lms.list_labs()
            if not labs:
                return "There are no labs available at the moment."
            titles = []
            for lab in labs:
                title = lab.get("title") or lab.get("name")
                if title:
                    titles.append(title)
            if not titles:
                return "I could not find any lab titles in the LMS."
            labs_str = "; ".join(titles)
            return f"The following labs are available: {labs_str}."
        except Exception as exc:
            return f"Error while listing labs: {exc}"

    # special-case: how many students are enrolled
    if "how many" in text and "student" in text and "enrolled" in text:
        try:
            learners = lms.get_learners()
            count = len(learners)
            return f"There are {count} students enrolled in the system."
        except Exception as exc:
            return f"Error while counting enrolled students: {exc}"

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]

    # first LLM call: decide which tools to use
    try:
        msg = call_llm_with_tools(messages, TOOLS)
    except Exception as exc:
        return f"LLM error while deciding which tools to call: {exc}"

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

    messages.append(msg)
    messages.extend(tool_results_messages)
    print(
        f"[summary] Feeding {len(tool_results_messages)} tool results back to LLM",
        file=sys.stderr,
    )

    # second LLM call: summarize tool results, но без падений по 500/таймауту
    try:
        final_msg = call_llm_with_tools(messages, TOOLS)
        content = final_msg.get("content") or ""
        if not isinstance(content, str):
            content = str(content)
        if content.strip():
            return content
        return "No answer from LLM."
    except Exception as exc:
        return f"LLM error while summarizing tool results: {exc}"
