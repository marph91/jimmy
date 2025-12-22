"""Helper functions for tags."""


def get_inline_tags(text: str, start_characters: list[str]) -> list[str]:
    """
    >>> get_inline_tags("# header", ["#"])
    []
    >>> get_inline_tags("### h3", ["#"])
    []
    >>> get_inline_tags("#tag", ["#"])
    ['tag']
    >>> get_inline_tags("#tag abc", ["#"])
    ['tag']
    >>> sorted(get_inline_tags("#tag @abc", ["#", "@"]))
    ['abc', 'tag']
    """
    # TODO: can possibly be combined with todoist.split_labels()
    tags = set()
    for word in text.split():
        if (
            any(word.startswith(char) for char in start_characters)
            and len(word) > 1
            # exclude words like "###"
            and any(char not in start_characters for char in word)
        ):
            tags.add(word[1:])
    return list(tags)
