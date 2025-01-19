import json


def read_json(file):
    with open(file, "r", encoding="utf-8") as f:
        return json.loads(f.read())


def write_json(path, content):
    with open(path, "w", encoding="utf-8") as file:
        file.write(json.dumps(content, ensure_ascii=False, indent=2))
