"""Product identifiers shared by APIs, presets and catalogue collection."""
import re
import unicodedata

PRODUCT_PATTERN = r'^(?:RJ|BJ|VJ)(?:[0-9]{8}|[0-9]{6})$'
PRODUCT_ID = re.compile(PRODUCT_PATTERN)
SOURCES = ('maniax', 'books', 'pro', 'soft')


def normalize_id(value: str) -> str:
    return unicodedata.normalize('NFKC', value).strip().upper() if isinstance(value, str) else value



def product_site(workno: str) -> str:
    return {'RJ': 'maniax', 'BJ': 'books', 'VJ': 'pro'}[workno[:2]]
