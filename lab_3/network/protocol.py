import json


def encode_message(message: dict) -> bytes:
    json_string = json.dumps(message, ensure_ascii=False)
    return (json_string + "\n").encode("utf-8")


def decode_messages(buffer: str):
    lines = buffer.split("\n")

    complete_messages = []
    for line in lines[:-1]:
        line = line.strip()
        if not line:
            continue

        try:
            complete_messages.append(json.loads(line))
        except json.JSONDecodeError:
            pass

    rest = lines[-1]
    return complete_messages, rest