import re
import os

file_path = "gracebot.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Pattern: "umbrella_fact_q<num>": "<digits><punct><space>"
pattern = r'("umbrella_fact_q\d+":\s*")[\d١٢٣٤٥٦٧٨٩٠]+[\.\-\s]+'
new_content = re.sub(pattern, r'\1', content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Done replacing.")
