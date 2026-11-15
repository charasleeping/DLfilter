"""Shared, dependency-free title lookup for maintenance and the packaged helper."""
import json
import ssl
import time
import urllib.error
import urllib.request

LOCALES = {'ENG': 'en_US', 'CHI_HANT': 'zh_TW', 'CHI_HANS': 'zh_CN'}
SOURCES = ('maniax', 'home', 'girls', 'girls-pro', 'books', 'pro', 'soft')


def title_url(workno, source, language):
    if source not in SOURCES or language not in LOCALES:
        raise ValueError('Unsupported title source or language')
    return f'https://www.dlsite.com/{source}/api/=/product.json?workno={workno}&locale={LOCALES[language]}'


def extract_title(data, original):
    title = data[0].get('work_name') if data else None
    if title is not None and not isinstance(title, str):
        raise ValueError('Invalid title response')
    return title if title and title != original else None


def fetch_title(workno, source, language, original, wait=time.sleep):
    # Frozen interpreters cannot rely on the build machine's OpenSSL CA path.
    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        context = ssl.create_default_context()
    url = title_url(workno, source, language)
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'DLFilter/2.1 title collector'})
            with urllib.request.urlopen(req, timeout=30, context=context) as response:
                return extract_title(json.load(response), original)
        except (OSError, ValueError) as exc:
            if attempt == 4:
                raise
            delay = 2 ** attempt
            if isinstance(exc, urllib.error.HTTPError) and exc.code in (403, 429):
                try:
                    delay = max(30 * 2 ** attempt, float(exc.headers.get('Retry-After', '0')))
                except ValueError:
                    delay = 30 * 2 ** attempt
            wait(min(delay, 600))
