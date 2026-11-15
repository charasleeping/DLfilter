"""Private frozen helper: JSON-lines protocol on stdin/stdout; no third-party modules."""
import json
from pathlib import Path
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from module.title_lookup import fetch_title


def main():
    for line in sys.stdin:
        try:
            task = json.loads(line)
            if not re.fullmatch(r'(?:RJ|BJ|VJ)(?:[0-9]{6}|[0-9]{8})', task['id']):
                raise ValueError('Invalid product ID')
            title = fetch_title(task['id'], task['source'], task['language'], task['original'])
            print(json.dumps({'title': title}), flush=True)
        except Exception as exc:
            print(json.dumps({'error': str(exc)}), flush=True)


if __name__ == '__main__':
    main()
