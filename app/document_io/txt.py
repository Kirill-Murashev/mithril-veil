"""Plain-text document I/O — placeholder for future document pipeline."""


def read_txt(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()
