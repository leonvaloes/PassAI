from pathlib import Path
import sys

from pypdf import PdfReader


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python scripts/extract_pdf_text.py <input.pdf> <output.txt>")
        return 2

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    reader = PdfReader(str(input_path))
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append(f"--- PAGE {index} ---\n{text.strip()}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n\n".join(pages).strip() + "\n", encoding="utf-8")
    print(f"Extracted {len(reader.pages)} page(s) to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
