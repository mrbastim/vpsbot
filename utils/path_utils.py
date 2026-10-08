import os


class UnsafePathError(ValueError):
    """Путь выходит за пределы разрешённого каталога."""


def safe_join(base: str, *parts: str) -> str:
    """Склеивает пути, не позволяя выйти за пределы base.

    Абсолютные части игнорируются, символы ``..`` не позволяют
    подняться выше base (после разыменования symlink).
    """
    base_real = os.path.realpath(base)
    target = os.path.realpath(os.path.join(base_real, *parts))
    if target != base_real and not target.startswith(base_real + os.sep):
        raise UnsafePathError(f"Путь {parts!r} выходит за пределы {base_real}")
    return target


def safe_filename(name: str) -> str:
    """Возвращает только базовое имя файла без символов пути."""
    cleaned = os.path.basename((name or "").replace("\\", "/").strip())
    if not cleaned or cleaned in {".", ".."}:
        raise UnsafePathError(f"Недопустимое имя файла: {name!r}")
    return cleaned
