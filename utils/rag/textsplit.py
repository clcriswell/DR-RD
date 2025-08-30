import re, textwrap

def clean(text: str) -> str:
    s = text.replace("\x00", "")
    s = re.sub(r"\s+\n", "\n", s)
    return s.strip()

def split(text: str, *, size=800, overlap=120) -> list[str]:
    text = clean(text)
    chunks, i = [], 0
    while i < len(text):
        j = min(len(text), i + size)
        k = text.rfind("\n", i + int(size * 0.6), j)
        if k == -1:
            k = j
        chunks.append(text[i:k].strip())
        i = max(k - overlap, i + 1)
    return [c for c in chunks if c]
