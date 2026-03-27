#!/usr/bin/env python3
"""
merge_pdfs.py — Merge all PDFs in a directory into a single document
=====================================================================
Usage:
  python3 merge_pdfs.py <input_directory> [output_file] [options]

Examples:
  python3 merge_pdfs.py ./01-RESPERSMAN
  python3 merge_pdfs.py ./01-RESPERSMAN merged.pdf
  python3 merge_pdfs.py ./01-RESPERSMAN --sort name
  python3 merge_pdfs.py ./01-RESPERSMAN --sort date --exclude "*_merged*"
  python3 merge_pdfs.py ./01-RESPERSMAN --recursive
  python3 merge_pdfs.py ./01-RESPERSMAN --output ../consolidated/respersman_merged.pdf

Options:
  --output FILE       Output path (default: <dir_name>_merged.pdf in input dir)
  --sort name|date|none  Sort order: name (default), date modified, or original
  --recursive         Include PDFs in subdirectories
  --exclude PATTERN   Glob pattern of filenames to skip (repeatable)
  --no-bookmarks      Skip adding per-file bookmarks to the output
  --dry-run           List files that would be merged without merging
"""

import argparse
import fnmatch
import sys
from datetime import datetime
from pathlib import Path

try:
    from pypdf import PdfWriter, PdfReader
except ImportError:
    sys.exit("pypdf is required: pip install pypdf")


# ── Helpers ──────────────────────────────────────────────────────────────────

def find_pdfs(directory: Path, recursive: bool) -> list[Path]:
    pattern = "**/*.pdf" if recursive else "*.pdf"
    return [p for p in directory.glob(pattern) if p.is_file()]


def filter_pdfs(pdfs: list[Path], exclude_patterns: list[str]) -> list[Path]:
    result = []
    for p in pdfs:
        if any(fnmatch.fnmatch(p.name, pat) for pat in exclude_patterns):
            continue
        result.append(p)
    return result


def sort_pdfs(pdfs: list[Path], sort_by: str) -> list[Path]:
    if sort_by == "name":
        return sorted(pdfs, key=lambda p: p.name.lower())
    if sort_by == "date":
        return sorted(pdfs, key=lambda p: p.stat().st_mtime)
    return pdfs  # "none" — preserve glob order


def is_valid_pdf(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            return f.read(4) == b"%PDF"
    except OSError:
        return False


def human_size(n_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} TB"


# ── Core merge ───────────────────────────────────────────────────────────────

def merge(
    pdfs: list[Path],
    output: Path,
    add_bookmarks: bool = True,
    dry_run: bool = False,
    password: str = "",
) -> None:

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_input = sum(p.stat().st_size for p in pdfs)

    print(f"\nPDF Merger")
    print(f"  Input files : {len(pdfs)}")
    print(f"  Input size  : {human_size(total_input)}")
    print(f"  Output      : {output}")
    print(f"  Bookmarks   : {'yes' if add_bookmarks else 'no'}")
    print(f"  Mode        : {'DRY RUN' if dry_run else 'merge'}")
    print()

    skipped = []
    included = []

    for i, pdf in enumerate(pdfs, 1):
        valid = is_valid_pdf(pdf)
        size  = human_size(pdf.stat().st_size)
        status = "ok" if valid else "SKIP (invalid PDF)"
        print(f"  [{i:>3}/{len(pdfs)}] {status:20s} {size:>10}  {pdf.name}")
        if valid:
            included.append(pdf)
        else:
            skipped.append(pdf)

    print()
    if skipped:
        print(f"  Skipping {len(skipped)} invalid file(s).")
        print()

    if dry_run:
        print(f"  DRY RUN — no file written.")
        print(f"  Would merge {len(included)} PDFs → {output}")
        return

    if not included:
        sys.exit("No valid PDFs to merge.")

    writer = PdfWriter()
    errors = []

    for pdf in included:
        try:
            reader = PdfReader(str(pdf), strict=False)

            # Handle encrypted PDFs — try supplied password then empty string
            # (many government PDFs are technically encrypted with no real password)
            if reader.is_encrypted:
                decrypted = False
                passwords_to_try = list(dict.fromkeys(
                    p for p in [password, ""] if p is not None
                ))
                for pwd in passwords_to_try:
                    try:
                        if reader.decrypt(pwd) >= 1:
                            decrypted = True
                            break
                    except Exception:
                        pass
                if not decrypted:
                    errors.append((pdf.name, "Encrypted — could not decrypt (password required)"))
                    print(f"  ⚠ Skipping {pdf.name}: encrypted, no password available")
                    continue

            dest_page = len(writer.pages)
            for page in reader.pages:
                writer.add_page(page)
            if add_bookmarks and reader.pages:
                writer.add_outline_item(
                    title=pdf.stem,
                    page_number=dest_page,
                )
        except Exception as e:
            errors.append((pdf.name, str(e)))
            print(f"  ⚠ Error reading {pdf.name}: {e}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "wb") as fh:
        writer.write(fh)

    out_size = output.stat().st_size
    print(f"  ✓ Merged {len(included) - len(errors)} PDFs")
    print(f"  ✓ Output : {output}")
    print(f"  ✓ Size   : {human_size(out_size)}")
    if errors:
        print(f"  ⚠ {len(errors)} file(s) had errors and were skipped")
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge all PDFs in a directory into one file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("directory",
        help="Directory containing PDFs to merge")
    parser.add_argument("--output", "-o", default="",
        help="Output file path (default: <dir>/<dirname>_merged.pdf)")
    parser.add_argument("--sort", choices=["name", "date", "none"], default="name",
        help="Sort order: name (default), date modified, or none")
    parser.add_argument("--recursive", "-r", action="store_true",
        help="Include PDFs in subdirectories")
    parser.add_argument("--exclude", "-x", action="append", default=[],
        metavar="PATTERN",
        help="Glob pattern of filenames to skip (e.g. '*_merged*'). Repeatable.")
    parser.add_argument("--no-bookmarks", action="store_true",
        help="Do not add per-file bookmarks in the output")
    parser.add_argument("--password", "-p", default="",
        help="Password to try when opening encrypted PDFs")
    parser.add_argument("--dry-run", "-n", action="store_true",
        help="List files that would be merged without writing output")
    args = parser.parse_args()

    directory = Path(args.directory).resolve()
    if not directory.is_dir():
        sys.exit(f"Error: '{directory}' is not a directory.")

    # Default output path
    if args.output:
        output = Path(args.output).resolve()
    else:
        output = directory / f"{directory.name}_merged.pdf"

    # Always exclude the output file itself to avoid merging into itself
    args.exclude.append(output.name)

    # Discover, filter, sort
    pdfs = find_pdfs(directory, args.recursive)
    pdfs = filter_pdfs(pdfs, args.exclude)
    pdfs = sort_pdfs(pdfs, args.sort)

    if not pdfs:
        sys.exit(f"No PDFs found in '{directory}'.")

    merge(
        pdfs=pdfs,
        output=output,
        add_bookmarks=not args.no_bookmarks,
        dry_run=args.dry_run,
        password=args.password,
    )


if __name__ == "__main__":
    main()
