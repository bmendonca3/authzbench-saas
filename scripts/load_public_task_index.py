import json
from pathlib import Path

def load_public_task_index(tasks_dir: Path) -> dict[str, dict]:
    if not tasks_dir.exists() or not tasks_dir.is_dir():
        raise ValueError(f"Tasks directory does not exist or is not a directory: {tasks_dir}")
    
    index = {}
    for path in tasks_dir.rglob("*.json"):
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON in task file {path.name}: {exc}") from exc
        
        task_id = data.get("id")
        if not task_id:
            raise ValueError(f"Task file {path.name} is missing the 'id' field")
        if not isinstance(task_id, str):
            raise ValueError(f"Task file {path.name} 'id' field must be a string, got {type(task_id).__name__}")
        
        if task_id in index:
            raise ValueError(f"Duplicate task ID '{task_id}' found in {path.name} and {index[task_id]['path'].name}")
        
        expected_vulnerable = data.get("expected_vulnerable")
        if expected_vulnerable is None:
            raise ValueError(f"Task '{task_id}' is missing 'expected_vulnerable' field")
        if not isinstance(expected_vulnerable, bool):
            raise ValueError(f"Task '{task_id}' 'expected_vulnerable' must be a boolean, got {type(expected_vulnerable).__name__}")
        
        control_type = data.get("control_type")
        if not expected_vulnerable:
            if control_type not in {"denial", "authorized_allow"}:
                raise ValueError(f"Task '{task_id}' is secure control but has invalid or missing 'control_type': {control_type}")
        else:
            if control_type is not None and control_type != "":
                raise ValueError(f"Task '{task_id}' is vulnerable but has 'control_type': {control_type}")
        
        index[task_id] = {
            "path": path,
            "data": data,
            "expected_vulnerable": expected_vulnerable,
            "control_type": control_type,
        }
    return index
