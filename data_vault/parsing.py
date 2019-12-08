def bool_or_str(value: str):
    if value == 'True':
        return True
    if value == 'False':
        return False
    return value


def clean_line(line: str) -> str:
    """Split/tokenize a line with keywords and parameters.

    TODO: rewrite using grammar or lexer?
    """
    pieces = ['']
    quote = ''
    prev = ''
    for c in line.strip():
        if quote:
            if prev != '\\' and c == quote:
                quote = ''
                pieces[-1] += c
                pieces.append('')
            else:
                pieces[-1] += c
        else:
            if c == '"' or c == "'":
                assert pieces[-1] == ''
                pieces[-1] += c
                quote = c
            elif c.isspace():
                if pieces[-1] != '' and pieces[-1][-1] != ',':
                    pieces.append('')
            elif c == '#':
                break
            else:
                pieces[-1] += c
        prev = c

    if pieces[-1] == '':
        pieces = pieces[:-1]

    return pieces


def parse_arguments(line, defaults):
    iterable = iter(clean_line(line))
    user_arguments = {key.lstrip('-'): next(iterable) for key in iterable}

    config = defaults.copy()
    for key in config:
        if key in user_arguments:
            config[key] = bool_or_str(user_arguments[key])
        else:
            short_key = key[0]
            if short_key in user_arguments:
                config[key] = bool_or_str(user_arguments[short_key])
    return config


def unquote(text):
    if text.startswith('"'):
        assert text.endswith('"')
        text = text[1:-1].replace(r'\"', '"')

    if text.startswith("'"):
        assert text.endswith("'")
        text = text[1:-1].replace(r"\'", "'")

    return text


def split_variables(variables: str):
    variables = [
        v.strip() for v in variables.split(',')
    ]
    for v in variables:
        assert v != '*'
    assert len(variables) >= 1
    return variables
