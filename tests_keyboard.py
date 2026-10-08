#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка клавиатуры файлов: лимит 64 байта, корректность callback, Back."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from keyboards import build_files_keyboard
from utils.callback_paths import resolve

fails = []


def check(name, cond, extra=""):
    print(("PASS  " if cond else "FAIL  ") + name + (f"   [{extra}]" if extra else ""))
    if not cond:
        fails.append(name)


def flatten(builder):
    return [b.callback_data for row in builder.export() for b in row]


BASE = tempfile.mkdtemp(prefix="vpsbot_kb_")
os.makedirs(os.path.join(BASE, "alpha", "beta"))
os.makedirs(os.path.join(BASE, "a" * 50))
os.makedirs(os.path.join(BASE, "a" * 50, "b" * 50, "c" * 50))
with open(os.path.join(BASE, "note.txt"), "w") as f:
    f.write("x")
with open(os.path.join(BASE, "имя файла.md"), "w") as f:
    f.write("x")

kb = build_files_keyboard(BASE, BASE)
data = flatten(kb)
check("root listing непустая", len(data) > 3, str(data))
check("root без back_to_dir", "back_to_main" in data, str(data))
check(
    "все callback <= 64b",
    all(len(d.encode()) <= 64 for d in data),
    max((len(d.encode()) for d in data), default=0),
)
check("нет 'back' как отдельной кнопки", "back" not in data)

for d in data:
    if d.startswith(("dir_", "file_")):
        try:
            resolved = resolve(d, BASE)
        except Exception as e:
            check(f"resolve {d}", False, repr(e))
            continue
        check(f"{d[:40]} существует", os.path.exists(resolved), resolved)

sub = os.path.join(BASE, "alpha")
kb2 = build_files_keyboard(sub, BASE, add_back=True)
d2 = flatten(kb2)
back = [d for d in d2 if "Back" not in d and d.startswith("dir_")]
check("sub: есть dir_beta", any(d == "dir_alpha/beta" for d in d2), str(d2))
check(
    "sub: Back указывает в родителя",
    any(d == "dir_." for d in d2) or any(resolve(d, BASE) == BASE for d in d2),
    str(d2),
)
check("sub: все callback <= 64b", all(len(d.encode()) <= 64 for d in d2))

deep = os.path.join(BASE, "a" * 50, "b" * 50, "c" * 50)
kb3 = build_files_keyboard(deep, BASE, add_back=True)
d3 = flatten(kb3)
check("deep: клавиатура собрана", bool(d3), str(d3)[:120])
check(
    "deep: все callback <= 64b",
    all(len(d.encode()) <= 64 for d in d3),
    max((len(d.encode()) for d in d3), default=0),
)
check(
    "deep: Back = один уровень выше",
    any(resolve(d, BASE) == os.path.dirname(deep) for d in d3 if d.startswith("dir_")),
    str(d3)[:200],
)

check(
    "юникодное имя в кнопке",
    any("имя файла.md" in b.text for row in kb.export() for b in row),
)

if fails:
    print(f"\n{len(fails)} FAILED: {fails}")
    sys.exit(1)
print("\nFILES KEYBOARD OK")
