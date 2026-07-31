# One-time script: Extract PHRASES + DIALECT_NAMES into grace_strings.py
# Then patch gracebot.py to import from it instead.
import sys

BOT = "gracebot.py"
OUT = "grace_strings.py"

with open(BOT, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Lines 109-624 (1-indexed) = indices 108..623
START, END = 108, 624
extracted = lines[START:END]

# Write grace_strings.py
with open(OUT, "w", encoding="utf-8") as f:
    f.write("# -*- coding: utf-8 -*-\n")
    f.write("# ══════════════════════════════════════════════════════════════════\n")
    f.write("# Grace Ashcroft Bot — Localization Strings & Persona Phrases\n")
    f.write("# Extracted from gracebot.py — DO NOT modify string content.\n")
    f.write("# ══════════════════════════════════════════════════════════════════\n\n")
    f.writelines(extracted)
    f.write("\n")

# Syntax-check the new file
try:
    compile(open(OUT, encoding="utf-8").read(), OUT, "exec")
    print(f"✅ {OUT} created — syntax OK")
except SyntaxError as e:
    print(f"❌ {OUT} has syntax error: {e}")
    sys.exit(1)

# Patch gracebot.py
new_lines = lines[:START]
new_lines.append("from grace_strings import PHRASES, DIALECT_NAMES\n")
new_lines.append("\n")
new_lines.extend(lines[END:])

# Syntax-check the patched bot
try:
    compile("".join(new_lines), BOT, "exec")
    print(f"✅ Patched {BOT} — syntax OK")
except SyntaxError as e:
    print(f"❌ Patched {BOT} has syntax error: {e} — ABORTING, no changes made")
    sys.exit(1)

with open(BOT, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"✅ Done. {len(lines)} → {len(new_lines)} lines ({len(lines)-len(new_lines)} moved to {OUT})")
