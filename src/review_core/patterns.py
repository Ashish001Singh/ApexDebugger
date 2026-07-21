import re
LOOP_OPEN = re.compile(r"\b(for|while)\b[^{]*\{|\bdo\b\s*\{", re.IGNORECASE)