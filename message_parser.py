class BadSegmentData(Exception): pass
class UnsupportedSegment(Exception): pass


def parse(message: list) -> dict:
    message_data = {"text": "", "file": []}
    for segment in message:
        try:
            match segment["type"]:
                case "text":
                    message_data["text"] += segment["data"]["text"]
                case "mention":
                    message_data["text"] += f"<@{segment['data']['user_id']}>"
                case _:
                    raise UnsupportedSegment
        except KeyError:
            raise BadSegmentData
    return message_data