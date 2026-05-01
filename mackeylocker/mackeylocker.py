#!/usr/bin/env python3
"""
mackeylocker — lock keyboard (and optionally Touch Bar) input on macOS
so you can wipe down your keys without firing off random shortcuts.

Unlock by clicking the on-screen button, holding all four modifier
keys at once, or triple-clicking the mouse.

Requires Accessibility permissions and root for Touch Bar control.
"""

import argparse
import os
import subprocess
import sys
import threading
import time

try:
    import Quartz
    from Quartz import (
        CFMachPortCreateRunLoopSource,
        CFRunLoopAddSource,
        CFRunLoopGetCurrent,
        CFRunLoopRun,
        CFRunLoopStop,
        CGEventGetFlags,
        CGEventMaskBit,
        CGEventTapCreate,
        CGEventTapEnable,
        kCFRunLoopCommonModes,
        kCGEventFlagMaskAlternate,
        kCGEventFlagMaskCommand,
        kCGEventFlagMaskControl,
        kCGEventFlagMaskShift,
        kCGEventFlagsChanged,
        kCGEventKeyDown,
        kCGEventKeyUp,
        kCGEventLeftMouseDown,
        kCGEventOtherMouseDown,
        kCGEventRightMouseDown,
        kCGHeadInsertEventTap,
        kCGSessionEventTap,
    )
except ImportError:
    print("pyobjc-framework-Quartz is required. Install it with:")
    print("  pip install pyobjc-framework-Quartz")
    sys.exit(1)

try:
    import tkinter as tk
except ImportError:
    print("Tkinter is required but not available in this Python install.")
    print("Use the system Python (/usr/bin/python3) or install python-tk.")
    sys.exit(1)


# ---- state ----

event_tap = None
run_loop = None
unlock_requested = threading.Event()
click_times = []

TRIPLE_CLICK_WINDOW = 1.0
ALL_MODIFIERS = (
    kCGEventFlagMaskShift
    | kCGEventFlagMaskControl
    | kCGEventFlagMaskAlternate
    | kCGEventFlagMaskCommand
)


# ---- touch bar ----

def disable_touch_bar():
    killed = False
    for proc in ("TouchBarServer", "ControlStrip"):
        result = subprocess.run(
            ["pkill", "-f", proc],
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        if result.returncode == 0:
            killed = True
    if killed:
        print("Touch Bar disabled.")
    else:
        print("No Touch Bar processes found (probably not a Touch Bar Mac).")


def enable_touch_bar():
    subprocess.run(
        ["killall", "ControlStrip"],
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )
    time.sleep(1)
    print("Touch Bar re-enabled.")


# ---- event tap ----

def request_unlock():
    unlock_requested.set()


def keyboard_callback(proxy, event_type, event, refcon):
    global click_times

    # all four modifiers held = unlock
    if event_type == kCGEventFlagsChanged:
        flags = CGEventGetFlags(event)
        if (flags & ALL_MODIFIERS) == ALL_MODIFIERS:
            print("Modifier combo detected, unlocking.")
            request_unlock()
            return None

    # triple-click = unlock (mouse events still pass through)
    if event_type in (kCGEventLeftMouseDown, kCGEventRightMouseDown, kCGEventOtherMouseDown):
        now = time.time()
        click_times.append(now)
        click_times = [t for t in click_times if now - t <= TRIPLE_CLICK_WINDOW]
        if len(click_times) >= 3:
            print("Triple-click detected, unlocking.")
            click_times.clear()
            request_unlock()
        return event

    # swallow keyboard events
    if event_type in (kCGEventKeyDown, kCGEventKeyUp):
        return None

    return event


def start_event_tap():
    global event_tap, run_loop

    mask = (
        CGEventMaskBit(kCGEventKeyDown)
        | CGEventMaskBit(kCGEventKeyUp)
        | CGEventMaskBit(kCGEventFlagsChanged)
        | CGEventMaskBit(kCGEventLeftMouseDown)
        | CGEventMaskBit(kCGEventRightMouseDown)
        | CGEventMaskBit(kCGEventOtherMouseDown)
    )

    event_tap = CGEventTapCreate(
        kCGSessionEventTap, kCGHeadInsertEventTap, 0,
        mask, keyboard_callback, None,
    )

    if event_tap is None:
        print("Failed to create event tap.")
        print("You need to grant Accessibility access:")
        print("  System Settings > Privacy & Security > Accessibility")
        request_unlock()
        return

    source = CFMachPortCreateRunLoopSource(None, event_tap, 0)
    run_loop = CFRunLoopGetCurrent()
    CFRunLoopAddSource(run_loop, source, kCFRunLoopCommonModes)
    CGEventTapEnable(event_tap, True)

    print("Keyboard locked.")
    CFRunLoopRun()


# ---- unlock ----

def do_unlock(touch_bar=True):
    global run_loop, event_tap
    if event_tap:
        CGEventTapEnable(event_tap, False)
    if run_loop:
        CFRunLoopStop(run_loop)
    if touch_bar:
        enable_touch_bar()
    print("Keyboard unlocked.")


# ---- ui ----

def build_ui(touch_bar=True):
    root = tk.Tk()
    root.title("MacKeylocker")
    root.attributes("-topmost", True)
    root.geometry("380x200+100+100")
    root.resizable(False, False)
    root.configure(bg="#1a1a2e")

    lock_msg = "Keyboard & Touch Bar locked" if touch_bar else "Keyboard locked"
    tk.Label(
        root, text=lock_msg,
        font=("Helvetica", 18, "bold"), fg="#e0e0e0", bg="#1a1a2e",
    ).pack(pady=(20, 5))

    tk.Label(
        root, text="unlock: button / cmd+opt+ctrl+shift / triple-click",
        font=("Helvetica", 11), fg="#888888", bg="#1a1a2e",
    ).pack(pady=(0, 15))

    def on_unlock():
        do_unlock(touch_bar=touch_bar)
        root.destroy()

    tk.Button(
        root, text="Unlock", font=("Helvetica", 15, "bold"),
        bg="#e94560", fg="white", activebackground="#ff6b6b",
        activeforeground="white", relief="flat", padx=20, pady=8,
        command=on_unlock,
    ).pack(pady=5)

    root.protocol("WM_DELETE_WINDOW", on_unlock)

    def poll():
        if unlock_requested.is_set():
            on_unlock()
        else:
            root.after(100, poll)

    root.after(100, poll)
    return root


# ---- timeout ----

def schedule_timeout(seconds, touch_bar):
    def _timer():
        time.sleep(seconds)
        print(f"Timeout ({seconds}s) reached, unlocking.")
        request_unlock()

    t = threading.Thread(target=_timer, daemon=True)
    t.start()


# ---- entry ----

def parse_args():
    parser = argparse.ArgumentParser(
        prog="mackeylocker",
        description="Lock keyboard and Touch Bar input while you clean your Mac.",
    )
    parser.add_argument(
        "--no-touchbar", action="store_true",
        help="skip Touch Bar locking (for Macs without a Touch Bar)",
    )
    parser.add_argument(
        "--timeout", type=int, default=None, metavar="SECONDS",
        help="auto-unlock after this many seconds",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.no_touchbar and os.geteuid() != 0:
        print("Root is needed to control the Touch Bar. Restarting with sudo...")
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

    touch_bar = not args.no_touchbar

    if touch_bar:
        disable_touch_bar()

    if args.timeout:
        schedule_timeout(args.timeout, touch_bar)

    tap_thread = threading.Thread(target=start_event_tap, daemon=True)
    tap_thread.start()

    root = build_ui(touch_bar=touch_bar)
    root.mainloop()


if __name__ == "__main__":
    main()
