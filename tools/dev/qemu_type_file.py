#!/usr/bin/env python3
"""Type the contents of a file into a QEMU guest via the HMP monitor.

Usage: qemu_type_file.py <text-file> <monitor-socket>
"""
import socket
import sys
import time

SPECIAL = {
    " ": "spc", "\n": "ret", "\t": "tab",
    "/": "slash", "\\": "backslash", "-": "minus", "=": "equal",
    ".": "dot", ",": "comma", ";": "semicolon", "'": "apostrophe",
    "[": "bracket_left", "]": "bracket_right",
    '"': "shift-apostrophe", ":": "shift-semicolon", "#": "shift-3",
    "(": "shift-9", ")": "shift-0", "_": "shift-minus", "+": "shift-equal",
    "*": "shift-8", "&": "shift-7", "%": "shift-5", "$": "shift-4",
    "!": "shift-1", "?": "shift-slash", "<": "shift-comma", ">": "shift-dot",
    "@": "shift-2", "^": "shift-6", "|": "shift-backslash", "~": "shift-grave",
    "{": "shift-bracket_left", "}": "shift-bracket_right",
}


def keyname(c):
    if c.isupper():
        return "shift-" + c.lower()
    if c.isdigit() or c.islower():
        return c
    if c in SPECIAL:
        return SPECIAL[c]
    raise ValueError(f"no key for {c!r}")


def main():
    text = open(sys.argv[1], encoding="utf-8").read().rstrip("\n")
    sock = sys.argv[2]
    s = socket.socket(socket.AF_UNIX)
    s.connect(sock)
    s.recv(200)
    for c in text:
        s.sendall(("sendkey %s\n" % keyname(c)).encode())
        time.sleep(0.035)
    s.sendall(b"sendkey ret\n")
    time.sleep(0.3)
    print("sent", len(text) + 1, "keys")


if __name__ == "__main__":
    main()
