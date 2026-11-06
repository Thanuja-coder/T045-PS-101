
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
COMMANDS_FILE = PROJECT_DIR / "data" / "commands.txt"


def parse_command(line, line_number):
    parts = [part.strip() for part in line.split("|")]

    return {
        "line_number": line_number,
        "action": parts[0],
        "arguments": parts[1:]
    }


def load_commands():
    commands = []

    with open(COMMANDS_FILE, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            command = parse_command(line, line_number)
            commands.append(command)

    return commands
