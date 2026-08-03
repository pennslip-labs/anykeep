import os
import sys

CURRENT_DIR = os.path.dirname(__file__)
SRC_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
sys.path.insert(0, SRC_PATH)

from keep_parser import KeepParser


def main() -> None:
    parser = KeepParser()
    notes = parser.list_notes()
    print(f"Found {len(notes)} notes")
    for note in notes[:5]:
        print(note.get("name"), note.get("title"))


if __name__ == "__main__":
    main()
