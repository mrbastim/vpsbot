"""Реестр коротких токенов для длинных callback_data.

Telegram ограничивает callback_data 64 байтами, поэтому длинные
относительные пути заменяются коротким токеном. Соответствие
токен -> путь хранится в памяти и сбрасывается при рестарте бота.
"""

import hashlib
import os
from collections import OrderedDict

from utils.path_utils import UnsafePathError, safe_join

MAX_ENTRIES = 4096
_tokens: "OrderedDict[str, str]" = OrderedDict()


def _token_for(prefix: str, relpath: str) -> str:
    digest = hashlib.sha1(f"{prefix}\x00{relpath}".encode()).hexdigest()[:16]
    return f"{prefix}t_{digest}"


def register(prefix: str, relpath: str, base_path: str) -> str:
    """Возвращает callback_data, запоминая связь токена с путём."""
    relpath = relpath.replace(os.sep, "/") if os.sep != "/" else relpath
    raw = f"{prefix}{relpath}"
    if len(raw.encode()) <= 64:
        return raw
    callback_data = _token_for(prefix, relpath)
    _tokens[callback_data] = safe_join(base_path, relpath)
    _tokens.move_to_end(callback_data)
    while len(_tokens) > MAX_ENTRIES:
        _tokens.popitem(last=False)
    return callback_data


def resolve(callback_data: str, base_path: str) -> str:
    """Восстанавливает абсолютный путь из callback_data."""
    prefix, _, raw = callback_data.partition("_")
    if raw.startswith("t_"):
        cached = _tokens.get(callback_data)
        if cached:
            return cached
        raise UnsafePathError(f"Путь для {callback_data} больше не актуален")
    return safe_join(base_path, raw.replace("/", os.sep))
