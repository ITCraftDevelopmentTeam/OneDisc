import re
import message_parser
import translator


def tokenizer(code):
    tokens = []
    matches = list(re.finditer(re.compile(r"\[CQ:[^\].]+\]", re.DOTALL), code))
    
    start = 0
    for match in matches:
        if match.start() > start:
            tokens.append(('text', code[start:match.start()]))
        tokens.append(('cqcode', match.group()))
        start = match.end()
    
    if start < len(code):
        tokens.append(('text', code[start:]))

    return tokens

# def parse_raw_message(raw_message: str) -> list:
#     return translator.translate_v12_message_to_v11(message_parser.parse_string(raw_message))

def parse_primary_string(string: str) -> str:
    return string.replace("&#91;", "[")\
        .replace("&#93;", "]")\
        .replace("&#44;", ",")

def parse_string_inside_cqcode(string: str) -> str | int | float | bool:
    parsed_string = string.replace("&amp;", "&")\
        .replace("&#91;", "[")\
        .replace("&#93;", "]")\
        .replace("&#44;", ",")
    try:
        if str(int(parsed_string)) == parsed_string:
            parsed_string = int(parsed_string)
        else:
            parsed_string = float(parsed_string)
    except ValueError:
        pass
    match parsed_string:
        case 1 | "y" | "yes" | "true" | "True" | "TRUE" | "t" | "T":
            parsed_string = True
        case 0 | "n" | "no" | "false" | "False" | "FALSE" | "f" | "F":
            parsed_string = False
    return parsed_string

def parse_string_to_array(string: str) -> list:
    tokens = tokenizer(string)
    message = []
    for token in tokens:
        if token[0] == "cqcode":
            cqcode = token[1][4:-1].split(",")
            _type = cqcode.pop(0)
            data = {}
            for raw_argv in cqcode:
                argv = raw_argv.split("=")
                data[parse_string_inside_cqcode(argv.pop(0))] = parse_string_inside_cqcode("=".join(argv))
            message.append({
                "type": _type,
                "data": data
            })
            del _type, data
        else:
            message.append({
                "type": "text",
                "data": {
                    "text": parse_primary_string(token[1])
                }
            })
    return message

if __name__ == "__main__":

    print(tokenizer("awa[CQ:at,qq=114514]]qwq"))
    print(tokenizer("awa[CQ:at,qq=114 514]]qwq"))
