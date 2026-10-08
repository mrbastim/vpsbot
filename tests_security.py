#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверки безопасности: path traversal, callback_data, роли, валидация."""

import html
import os
import re
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE = tempfile.mkdtemp(prefix="vpsbot_test_")
SECRET = os.path.join(os.path.dirname(BASE), "secret_outside.txt")
with open(SECRET, "w") as f:
    f.write("top secret")
os.makedirs(os.path.join(BASE, "vpn_configs"), exist_ok=True)
with open(os.path.join(BASE, "vpn_configs", "client.ovpn"), "w") as f:
    f.write("client config")

from utils.admin_service import AdminService
from utils.callback_paths import register, resolve
from utils.path_utils import UnsafePathError, safe_filename, safe_join

fails = []


def check(name, cond, extra=""):
    print(("PASS  " if cond else "FAIL  ") + name + (f"   [{extra}]" if extra else ""))
    if not cond:
        fails.append(name)


def rel(*parts):
    return os.path.relpath(SECRET, BASE).replace(os.sep, "/")


print("=== path traversal: чтение файлов вне /root ===")
for evil in (
    rel(),
    "../" * 3 + "etc/shadow",
    "../../../etc/passwd",
    "..",
    "a/../../.." + "/" + os.path.basename(SECRET),
    os.path.abspath(SECRET),
    "/etc/shadow",
    "vpn_configs/../../.." + "/" + os.path.basename(SECRET),
):
    try:
        got = safe_join(BASE, evil)
        check(f"blocks {evil!r}", False, f"-> {got}")
    except UnsafePathError:
        check(f"blocks {evil!r}", True)

for good, expect in (
    ("vpn_configs", os.path.join(BASE, "vpn_configs")),
    ("vpn_configs/client.ovpn", os.path.join(BASE, "vpn_configs", "client.ovpn")),
    (".", BASE),
    ("", BASE),
    ("./.", BASE),
):
    check(f"allows {good!r}", safe_join(BASE, good) == expect)

try:
    safe_join(BASE, "sub", "..", "..", os.path.basename(SECRET))
    check("blocks escape via sub", False)
except UnsafePathError:
    check("blocks escape via sub", True)

print()
print("=== symlink escape ===")
try:
    link = os.path.join(BASE, "escape_link")
    os.symlink(SECRET, link)
    try:
        safe_join(BASE, "escape_link")
        check("blocks symlink out of base", False)
    except UnsafePathError:
        check("blocks symlink out of base", True)
except (OSError, NotImplementedError, AttributeError):
    check("blocks symlink out of base", True, "symlinks unavailable, skipped")

print()
print("=== upload filename sanitisation ===")
for evil, expect in (
    ("../../etc/cron.d/pwn", "pwn"),
    ("..\\..\\windows\\system32\\evil.bat", "evil.bat"),
    ("/etc/passwd", "passwd"),
    ("normal.ovpn", "normal.ovpn"),
    ("a/b/c/deep.txt", "deep.txt"),
):
    got = safe_filename(evil)
    check(f"sanitizes {evil!r}", got == expect, f"-> {got!r}")

for bad in ("", "   ", ".", "..", None, "/", "//", "....//"):
    try:
        safe_filename(bad)
        check(f"rejects {bad!r}", False)
    except UnsafePathError:
        check(f"rejects {bad!r}", True)

print()
print("=== callback_data <= 64 байт ===")
long_rel = "/".join(["averylongdirectoryname"] * 6) + "/client.conf"
cd = register("file_", long_rel, BASE)
check("long path tokenised", len(cd.encode()) <= 64, f"{len(cd.encode())}b {cd}")
check(
    "token resolves back",
    resolve(cd, BASE) == os.path.realpath(os.path.join(BASE, long_rel)),
)
short_cd = register("file_", "client.ovpn", BASE)
check("short path inlined", short_cd == "file_client.ovpn", short_cd)
check("short resolves", resolve(short_cd, BASE) == os.path.join(BASE, "client.ovpn"))
try:
    resolve("file_t_0000000000000000", BASE)
    check("unknown token rejected", False)
except UnsafePathError:
    check("unknown token rejected", True)
try:
    resolve("file_" + "../" * 10 + "x", BASE)
    check("forged traversal token rejected", False)
except UnsafePathError:
    check("forged traversal token rejected", True)
ok = True
for prefix in ("file_", "dir_"):
    for depth in range(1, 60):
        if (
            len(
                register(
                    prefix, "/".join("x" * 40 for _ in range(depth)), BASE
                ).encode()
            )
            > 64
        ):
            ok = False
            break
check("any depth stays <= 64b", ok)

print()
print("=== роли: пользователь != админ ===")
db = os.path.join(BASE, "access.db")
import config

saved_admins = config.ADMIN_IDS
config.ADMIN_IDS = ["423417426"]
svc = AdminService(db)
ADMIN, USER, GUEST = 423417426, 999000111, 999000222

check("config admin is admin", svc.is_admin(ADMIN))
check("unknown user blocked", not svc.exists(GUEST))
check("add as plain user", svc.add(USER, is_admin=False))
check("plain user exists", svc.exists(USER))
check("plain user NOT admin", not svc.is_admin(USER))
check("duplicate add -> False", not svc.add(USER, is_admin=False))

fresh = AdminService(db)
check("роль пережила рестарт", fresh.exists(USER) and not fresh.is_admin(USER))
check("promote to admin", AdminService(db).add(GUEST, is_admin=True))
check("promoted is admin", AdminService(db).is_admin(GUEST))
check("remove user", fresh.remove(USER))
check("removed is gone", not AdminService(db).exists(USER))
check("cannot remove config admin effect", svc.is_admin(ADMIN))

print()
print("=== миграция со старой схемы без is_admin ===")
legacy = os.path.join(BASE, "legacy.db")
with sqlite3.connect(legacy) as c:
    c.execute("CREATE TABLE allowed_users (user_id INTEGER PRIMARY KEY)")
    c.execute("INSERT INTO allowed_users (user_id) VALUES (777)")
    c.commit()
migrated = AdminService(legacy)
check("legacy user survives", migrated.exists(777))
check("legacy user not admin", not migrated.is_admin(777))
check("legacy admin seeded", migrated.is_admin(ADMIN))

print()
print("=== валидация имени VPN-клиента ===")
CLIENT_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
for good in ("client1", "my-client", "my_client", "a" * 32):
    check(f"accepts {good[:24]!r}", bool(CLIENT_NAME_RE.match(good)))
for bad in (
    "../evil",
    "a;rm -rf /",
    "a b",
    "a\nb",
    "x" * 33,
    "",
    "$(id)",
    "`id`",
    "a|b",
    "*",
    "a&b",
    "a'b",
):
    check(f"rejects {bad!r}", not CLIENT_NAME_RE.match(bad))

print()
print("=== HTML/MarkdownV2 escaping ===")
raw = "client <b>&</b> \"q\" 'a'"
check("html escaped", "<b>" not in html.escape(raw), html.escape(raw))
for ch, escaped in (("`", "\\`"), ("\\", "\\\\")):
    got = ch.replace("\\", "\\\\").replace("`", "\\`")
    check(f"{ch!r} escaped in MarkdownV2", got == escaped, repr(got))

print()
print("=== middleware: белый список и роль админа ===")
import asyncio

from middlewares.access import AccessMiddleware, AdminMiddleware


class FakeUser:
    def __init__(self, uid):
        self.id = uid


class FakeAnswer:
    def __init__(self):
        self.text = None
        self.answers = 0

    async def answer(self, text=None, **kw):
        if text:
            self.text = text
        self.answers += 1


class FakeEvent:
    def __init__(self, uid, is_callback=False):
        self.from_user = FakeUser(uid)
        self._ans = FakeAnswer()
        self.message = self
        self.is_callback = is_callback

    async def answer(self, text=None, **kw):
        await self._ans.answer(text, **kw)


async def _run_mw(mw, event):
    called = {"hit": False}

    async def handler(_event, _data):
        called["hit"] = True
        return "ok"

    res = await mw(handler, event, {})
    return called["hit"], res, event._ans.text


svc = AdminService(db)
plain = 999111222
svc.add(plain, is_admin=False)


STRANGER = 424242424


async def _mw_checks():
    hit, _, text = await _run_mw(AccessMiddleware(svc), FakeEvent(STRANGER))
    check("AccessMiddleware blocks stranger", not hit and text is not None)
    hit, _, text = await _run_mw(AccessMiddleware(svc), FakeEvent(STRANGER, True))
    check(
        "AccessMiddleware blocks stranger (callback)",
        not hit and "доступа" in (text or ""),
    )
    hit, _, text = await _run_mw(AccessMiddleware(svc), FakeEvent(plain))
    check("AccessMiddleware allows plain user", hit and text is None)
    hit, _, text = await _run_mw(AdminMiddleware(svc), FakeEvent(plain))
    check("AdminMiddleware blocks plain user", not hit and "прав" in (text or ""))
    hit, _, text = await _run_mw(AdminMiddleware(svc), FakeEvent(ADMIN))
    check("AdminMiddleware allows admin", hit and text is None)
    hit, _, text = await _run_mw(AdminMiddleware(svc), FakeEvent(ADMIN, True))
    check("AdminMiddleware allows admin (callback)", hit and text is None)


asyncio.run(_mw_checks())

print()
print("=== импорт всех модулей ===")
import importlib

for mod in (
    "utils.path_utils",
    "utils.callback_paths",
    "utils.admin_service",
    "utils.docker_manager",
    "utils.service_manager",
    "middlewares.access",
    "keyboards",
):
    try:
        importlib.import_module(mod)
        check(f"import {mod}", True)
    except Exception as e:
        check(f"import {mod}", False, repr(e))

config.ADMIN_IDS = saved_admins
print()
if fails:
    print(f"{len(fails)} FAILED: {fails}")
    sys.exit(1)
print("ALL TESTS PASSED")
