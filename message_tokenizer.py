import re

def tokenizer(code):
    # 定义正则表达式模式
    token_patterns = {
        'mention': '<@[0-9]+>',
        'mention_all': '@everyone',
        'text': '.+'
    }
    
    tokens = []
    code_remaining = code

    while code_remaining:
        matched = False
        for token_type, pattern in token_patterns.items():
            match = re.match(pattern, code_remaining)
            if match:
                token_value = match.group(0)
                tokens.append((token_type, token_value))
                code_remaining = code_remaining[len(token_value):]
                matched = True
                break
        
        if not matched:
            raise ValueError(f"Unexpected character: '{code_remaining[0]}'")
    
    return tokens
