def parse_text(string: str) -> list:
    segment = [{
        "type": "text",
        "data": {
            "text": string
        }
    }]
    return segment