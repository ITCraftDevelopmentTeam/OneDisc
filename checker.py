class BadParam(Exception): pass

def check_aruments(*args) -> None:
    if None in args:
        raise BadParam("None is not allowed")