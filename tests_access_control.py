#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Проверка, что admin-only обработчики закрыты AdminMiddleware."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

config.path_pc_global = "/root"

import handlers.callbacks as cb
import handlers.commands as cm

fails = []


def check(name, cond, extra=""):
    print(("PASS  " if cond else "FAIL  ") + name + (f"   [{extra}]" if extra else ""))
    if not cond:
        fails.append(name)


def names(observer):
    return sorted(h.callback.__name__ for h in observer.handlers)


for label, router, observers in (
    ("commands", cm.admin_router, ("message",)),
    ("callbacks", cb.admin_callbacks_router, ("message", "callback_query")),
):
    for name in observers:
        observer = getattr(router, name)
        attached = [type(m).__name__ for m in observer.middleware]
        check(
            f"admin/{label}.{name}: AdminMiddleware attached",
            attached == ["AdminMiddleware"],
            attached,
        )
        check(
            f"admin/{label}.{name}: есть хендлеры",
            bool(names(observer)),
            ", ".join(names(observer)),
        )

for label, router in (
    ("commands", cm.commands_router),
    ("callbacks", cb.callbacks_router),
):
    for name in ("message", "callback_query"):
        observer = getattr(router, name, None)
        if observer is None:
            continue
        check(f"public/{label}.{name}: без AdminMiddleware", not observer.middleware)

public = set()
for router in (cm.commands_router, cb.callbacks_router):
    for name in ("message", "callback_query"):
        observer = getattr(router, name, None)
        if observer:
            public.update(names(observer))

banned = {
    "files_handler",
    "vpn_handler",
    "cmd_add_admin_start",
    "process_docker_status_callback",
    "process_services_status_callback",
    "listfiles_markup",
    "handle_document_upload",
    "process_system_info_callback",
    "refresh_sysinfo_handler",
}
leaked = public & banned
check("приватные хендлеры не в публичных роутерах", not leaked, sorted(leaked))

check("публичный /start доступен всем", "send_welcome" in public)
check("add_admin завершение в публичном роутере", "cmd_add_admin_finish" in public)

if fails:
    print(f"\n{len(fails)} FAILED: {fails}")
    sys.exit(1)
print("\nACCESS CONTROL LAYOUT OK")
