class BadSegmentData(Exception): pass
class UnsupportedSegment(Exception): pass


def parse_message(message: list) -> dict:
    message_data = {"content": "", "file": []}
    for segment in message:
        try:
            match segment["type"]:
                case "text":
                    message_data["content"] += segment["data"]["text"]
                case "mention":
                    message_data["content"] += f"<@{segment['data']['user_id']}>"
                case _:
                    raise UnsupportedSegment
        except KeyError:
            raise BadSegmentData
    return message_data

def parse_string(string: str, file: list = []) -> list:
    # TODO
    return [{
        "type": "text",
        "data": {
            "text": string
        }
    }]
