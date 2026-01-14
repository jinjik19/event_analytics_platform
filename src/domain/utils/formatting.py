import re


_capital_letter_regex = re.compile("([A-Z])")


def split_camel_case(value: str) -> list[str]:
    return _capital_letter_regex.sub(r" \1", value).strip().lower().split()
