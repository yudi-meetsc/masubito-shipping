import json


def event(step: str, pct: int, message: str, **extra) -> str:
    payload = {"step": step, "pct": pct, "message": message, **extra}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
