from datetime import UTC, datetime
from pathlib import Path


def log_info(message: str, file_name: str = "") -> None:
    now = datetime.now(UTC)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    log_file_name = file_name if file_name else f"{now:%Y-%m-%d}.log"
    log_file = log_dir / log_file_name
    line = f"{now: %Y-%m-%d %H:%M:%S} - {message}\n"

    print(line)

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")
