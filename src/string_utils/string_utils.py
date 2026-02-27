"""
string_utils.py — String manipulation utilities module.
"""

import re


def truncate(text: str, max_len: int, suffix: str = "...") -> str:
    """
    Truncate text to fit within max_len including the suffix.

    If the text is longer than max_len, it is truncated so that the total
    length (text + suffix) equals exactly max_len.

    Args:
        text: The string to truncate.
        max_len: The maximum total length allowed.
        suffix: The suffix to append if truncation occurs (default: '...').

    Returns:
        The original text if its length <= max_len, otherwise the truncated
        text with suffix appended, fitting exactly to max_len characters.

    Examples:
        >>> truncate("Hello World", 8)
        'Hello...'
        >>> truncate("Hi", 5)
        'Hi'
    """
    if len(text) <= max_len:
        return text

    # If max_len <= len(suffix), return truncated suffix
    if max_len <= len(suffix):
        return suffix[:max_len]

    # Calculate how many chars from text we can keep
    available_len = max_len - len(suffix)
    return text[:available_len] + suffix


def slugify(text: str) -> str:
    """
    Convert text to a URL-friendly slug.

    Converts to lowercase, replaces spaces and underscores with hyphens,
    removes non-alphanumeric characters (except hyphens), collapses
    consecutive hyphens, and strips leading/trailing hyphens.

    Args:
        text: The string to convert to slug format.

    Returns:
        A lowercased, hyphenated slug.

    Examples:
        >>> slugify("Hello World! Foo & Bar")
        'hello-world-foo-bar'
        >>> slugify("__Hello__World__")
        'hello-world'
    """
    # Convert to lowercase
    slug = text.lower()

    # Replace spaces and underscores with hyphens
    slug = re.sub(r"[\s_]+", "-", slug)

    # Remove all characters that are not alphanumeric or hyphens
    slug = re.sub(r"[^a-z0-9\-]", "", slug)

    # Collapse consecutive hyphens to a single hyphen
    slug = re.sub(r"-+", "-", slug)

    # Strip leading and trailing hyphens
    slug = slug.strip("-")

    return slug


def count_words(text: str) -> int:
    """
    Count the number of whitespace-delimited words in text.

    Args:
        text: The string to count words in.

    Returns:
        The number of words, or 0 if text is empty or contains only whitespace.

    Examples:
        >>> count_words("Hello World")
        2
        >>> count_words("")
        0
    """
    return len(text.split())


def title_case(text: str) -> str:
    """
    Capitalize each word, with exceptions for small words when not first.

    Small words that are NOT capitalized (unless they are the first word):
    a, an, the, in, on, at, for, to, of

    Args:
        text: The string to convert to title case.

    Returns:
        The text with appropriate capitalization.

    Examples:
        >>> title_case("the lord of the rings")
        'The Lord of the Rings'
        >>> title_case("alice in wonderland")
        'Alice in Wonderland'
    """
    small_words = {"a", "an", "the", "in", "on", "at", "for", "to", "of"}

    words = text.split()
    if not words:
        return text

    # Process each word
    result = []
    for i, word in enumerate(words):
        if i == 0:
            # First word is always capitalized
            result.append(word.capitalize())
        elif word.lower() in small_words:
            # Small word not at the start stays lowercase
            result.append(word.lower())
        else:
            # Regular word is capitalized
            result.append(word.capitalize())

    return " ".join(result)
