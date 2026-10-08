#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка, что тексты бота не роняют отправку из-за разметки.

Раньше динамические значения вставлялись в MarkdownV2 без экранирования
зарезервированных символов (`.`, `!`, `-` и т.д.), и Telegram отвечал
`Bad Request: can't parse entities`. Теперь весь динамический текст
уходит в HTML `<pre>` через html.escape.
"""

import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

config.path_pc_global = "/root"

import handlers.callbacks as cb
import handlers.commands as cm

fails = []

RESERVED = set("_*[]()~`>#+-=|{}.!")


def check(name, cond, extra=""):
    print(("PASS  " if cond else "FAIL  ") + name + (f"   [{extra}]" if extra else ""))
    if not cond:
        fails.append(name)


def valid_html(text: str) -> bool:
    """В HTML-режиме Telegram необработанными остаются только < > &."""
    without_tags = re.sub(r"</?pre>", "", text)
    depth = 0
    i = 0
    while i < len(without_tags):
        ch = without_tags[i]
        if ch == "&":
            entity = re.match(r"&(#\d+|#x[0-9a-fA-F]+|[a-zA-Z]+);", without_tags[i:])
            if not entity:
                return False
            i += len(entity.group(0))
            continue
        if ch == "<":
            if not re.match(r"</?[a-zA-Z][^>]*>", without_tags[i:]):
                return False
            depth += 1
            i += 1
            continue
        i += 1
    return depth >= 0


print("=== _pre экранирует всё ===")
check("pre доступна в commands", hasattr(cm, "_pre"))
check("pre доступна в callbacks", hasattr(cb, "_pre"))

for evil in (
    "file.txt",
    "a<b>c",
    "a&b",
    "<script>alert(1)</script>",
    "100% & > 50",
    "quote's \" here",
    "моё_имя-файла.tar.gz",
):
    got = cm._pre(evil)
    check(
        f"pre({evil!r}) экранирует спецсимволы",
        html.escape(evil, quote=False) in got,
        got,
    )
    check(f"pre({evil!r}) валидный HTML", valid_html(got), got)

print()
print("=== реальные тексты хендлеров ===")


# show_commands отправляет текст без parse_mode — MarkdownV2 там не применяется.
def uses_markdown_v2(path: str) -> list[str]:
    """Строки, реально переключающие parse_mode на MarkdownV2."""
    pattern = re.compile(
        r"""parse_mode\s*=\s*["']MarkdownV2["']|ParseMode\.MARKDOWN_V2"""
    )
    found = []
    for num, line in enumerate(open(path, encoding="utf-8"), 1):
        if pattern.search(line):
            found.append(f"{os.path.basename(path)}:{num}")
    return found


check(
    "commands.py не использует MarkdownV2",
    not uses_markdown_v2(cm.__file__),
    uses_markdown_v2(cm.__file__),
)
check(
    "callbacks.py не использует MarkdownV2",
    not uses_markdown_v2(cb.__file__),
    uses_markdown_v2(cb.__file__),
)

print()
print("=== parse_mode=HTML всегда через _pre ===")
BAD_HTML = re.compile(r"""parse_mode\s*=\s*["']HTML["']""")
ASSIGN_FROM_PRE = re.compile(r"^(\s*)(\w+)\s*=\s*_pre\(")

for mod in (cm, cb):
    lines = open(mod.__file__, encoding="utf-8").read().splitlines()
    safe_names: set[str] = set()
    offenders = []
    for i, line in enumerate(lines):
        assign = ASSIGN_FROM_PRE.match(line)
        if assign:
            safe_names.add(assign.group(2))
        if not BAD_HTML.search(line):
            continue
        window = "\n".join(lines[max(0, i - 4) : i + 1])
        escaped = "_pre(" in window or "html.escape" in window
        escaped = escaped or any(
            re.search(rf"\b{name}\b", window) for name in safe_names
        )
        if not escaped:
            offenders.append(f"{os.path.basename(mod.__file__)}:{i + 1}")
    label = "commands" if mod is cm else "callbacks"
    check(f"{label}: HTML-ответы экранированы", not offenders, offenders)

print()
print("=== пути с спецсимволами в <pre> ===")
for path in ("/root/my_file.txt", "/root/a&b/c<d>.ovpn", "/root/100%.conf"):
    body = f"Path: {path}"
    check(f"pre безопасен для {path!r}", valid_html(cm._pre(body)), cm._pre(body))

print()
print("=== списки файлов ===")
listing = "\n".join(f"FILE\t{line[1:]}" for line in os.listdir("."))
check("список каталога валиден", valid_html(cm._pre(listing)))

if fails:
    print(f"\n{len(fails)} FAILED: {fails}")
    sys.exit(1)
print("\nMESSAGE FORMATTING OK")
