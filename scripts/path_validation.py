from pathlib import Path

def resolve_relative_inside(base: Path, raw: str, *, label: str) -> Path:
    if not raw or not raw.strip():
        raise ValueError(f"{label} must be non-empty")
    candidate = Path(raw)
    if candidate.is_absolute():
        raise ValueError(f"{label} must be relative: {raw}")
    if any(part == ".." for part in candidate.parts):
        raise ValueError(f"{label} must not contain '..': {raw}")
    resolved = (base / candidate).resolve()
    base_resolved = base.resolve()
    try:
        resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError(f"{label} escapes expected base directory: {raw}") from exc
    return resolved
