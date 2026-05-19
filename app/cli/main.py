"""Mithril Veil command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app import __version__
from app.core.exceptions import (
    InvalidAnonymizationMode,
    MithrilVeilError,
    UnsafeFileOperation,
    UnsupportedDocumentType,
)
from app.core.pipeline import run_anonymization
from app.core.report import write_anonymization_report
from app.core.schemas import AnonymizeMode
from app.document_io import (
    ensure_safe_output_path,
    ensure_safe_report_path,
    read_text_file,
    write_text_file,
)

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_UNSAFE = 2


def _parse_mode(value: str) -> AnonymizeMode:
    try:
        return AnonymizeMode(value)
    except ValueError as exc:
        raise InvalidAnonymizationMode(
            f"Invalid mode: {value!r}. Use 'replace' or 'redact'."
        ) from exc


def _print_stderr_summary(response) -> None:
    counts = response.summary.entity_counts
    if not counts:
        return
    types = ", ".join(sorted(counts))
    total = response.summary.total_entities
    print(f"Detected {total} entit{'y' if total == 1 else 'ies'} ({types}).", file=sys.stderr)


def _cmd_version(_args: argparse.Namespace) -> int:
    print(f"Mithril Veil {__version__}")
    return EXIT_SUCCESS


def _cmd_anonymize_text(args: argparse.Namespace) -> int:
    if not args.text.strip():
        print("Error: --text must not be empty.", file=sys.stderr)
        return EXIT_ERROR
    mode = _parse_mode(args.mode)
    response = run_anonymization(args.text, mode)
    _print_stderr_summary(response)
    sys.stdout.write(response.text)
    return EXIT_SUCCESS


def _cmd_anonymize_stdin(args: argparse.Namespace) -> int:
    mode = _parse_mode(args.mode)
    try:
        raw = sys.stdin.read()
    except OSError as exc:
        print(f"Error: cannot read stdin: {exc}", file=sys.stderr)
        return EXIT_ERROR
    if not raw.strip():
        print("Error: stdin input is empty.", file=sys.stderr)
        return EXIT_ERROR
    response = run_anonymization(raw, mode)
    _print_stderr_summary(response)
    sys.stdout.write(response.text)
    return EXIT_SUCCESS


def _cmd_anonymize_file(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)
    mode = _parse_mode(args.mode)
    force = bool(args.force)

    ensure_safe_output_path(input_path, output_path, force=force)
    if args.report:
        ensure_safe_report_path(Path(args.report), force=force)

    try:
        content = read_text_file(input_path)
    except UnsupportedDocumentType as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_UNSAFE
    except MithrilVeilError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    response = run_anonymization(content, mode)
    write_text_file(output_path, response.text, force=force)

    if args.report:
        report_path = Path(args.report)
        try:
            write_anonymization_report(report_path, response, mode, force=force)
        except UnsafeFileOperation as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return EXIT_UNSAFE
        except MithrilVeilError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return EXIT_ERROR

    _print_stderr_summary(response)
    return EXIT_SUCCESS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mithril-veil",
        description="Self-hosted Russian PII anonymization for safer AI workflows.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version", help="Print version and exit")

    text_parser = subparsers.add_parser("anonymize-text", help="Anonymize inline text")
    text_parser.add_argument("--text", required=True, help="Input text to anonymize")
    text_parser.add_argument(
        "--mode",
        default="replace",
        choices=[m.value for m in AnonymizeMode],
        help="Anonymization mode (default: replace)",
    )

    stdin_parser = subparsers.add_parser("anonymize-stdin", help="Anonymize text from stdin")
    stdin_parser.add_argument(
        "--mode",
        default="replace",
        choices=[m.value for m in AnonymizeMode],
        help="Anonymization mode (default: replace)",
    )

    file_parser = subparsers.add_parser("anonymize-file", help="Anonymize a text/markdown file")
    file_parser.add_argument("--input", required=True, help="Input file path (.txt, .md)")
    file_parser.add_argument("--output", required=True, help="Output file path")
    file_parser.add_argument(
        "--mode",
        default="replace",
        choices=[m.value for m in AnonymizeMode],
        help="Anonymization mode (default: replace)",
    )
    file_parser.add_argument("--report", help="Optional safe JSON report path")
    file_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output or report files",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "version": _cmd_version,
        "anonymize-text": _cmd_anonymize_text,
        "anonymize-stdin": _cmd_anonymize_stdin,
        "anonymize-file": _cmd_anonymize_file,
    }

    try:
        return handlers[args.command](args)
    except InvalidAnonymizationMode as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except UnsafeFileOperation as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_UNSAFE
    except MithrilVeilError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
