import argparse
import sys

from .organizer import DEFAULT_MODEL, organize_notes


def main() -> None:
    p = argparse.ArgumentParser(description="Group scattered notes under topic headings (Markdown output).")
    p.add_argument("input", nargs="?", help="Notes file. Omit to read from stdin (paste, then Ctrl+D).")
    p.add_argument("-o", "--output", help="Write Markdown to this file instead of stdout.")
    p.add_argument("-b", "--backend", choices=["auto", "llm", "local"], default="auto")
    p.add_argument("-m", "--model", default=DEFAULT_MODEL, help="Claude model (llm backend).")
    args = p.parse_args()

    text = open(args.input, encoding="utf-8").read() if args.input else sys.stdin.read()
    md = organize_notes(text, backend=args.backend, model=args.model)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Saved to {args.output}")
    else:
        print(md)


if __name__ == "__main__":
    main()
