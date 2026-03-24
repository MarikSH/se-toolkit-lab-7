from typing import Any, Dict, List, Tuple

import httpx

from config import lms_config


def _auth_headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {lms_config.api_key}"}


def check_health() -> Tuple[bool, str]:
    try:
        resp = httpx.get(
            f"{lms_config.base_url}/items/",
            headers=_auth_headers(),
            timeout=5.0,
        )
        resp.raise_for_status()
        items = resp.json()
        count = len(items) if isinstance(items, list) else 0
        return True, f"Backend is healthy. {count} items available."
    except httpx.HTTPError as exc:
        return False, f"Backend error: {exc}"
    except Exception as exc:
        return False, f"Backend error: {exc}"


def list_labs() -> List[Dict[str, Any]]:
    resp = httpx.get(
        f"{lms_config.base_url}/items/",
        headers=_auth_headers(),
        timeout=5.0,
    )
    resp.raise_for_status()
    items = resp.json()
    labs: List[Dict[str, Any]] = []
    if isinstance(items, list):
        for item in items:
            if item.get("type") == "lab":
                labs.append(item)
    return labs


def get_pass_rates(lab_id: str) -> List[Dict[str, Any]]:
    resp = httpx.get(
        f"{lms_config.base_url}/analytics/pass-rates",
        params={"lab": lab_id},
        headers=_auth_headers(),
        timeout=5.0,
    )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    return []
