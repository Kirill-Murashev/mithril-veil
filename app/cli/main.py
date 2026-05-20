"""Mithril Veil command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app import __version__
from app.cli.batch_cmd import cmd_anonymize_dir
from app.core.exceptions import (
    EmptyExtractedText,
    EncryptedDocumentUnsupported,
    InputFileTooLarge,
    InvalidAnonymizationMode,
    InvalidEncryptedMappingPath,
    MappingPassphraseMissing,
    MithrilVeilError,
    UnsafeFileOperation,
    UnsupportedDocumentType,
)
from app.core.mapping import PseudonymizationSession
from app.core.pipeline import run_anonymization
from app.core.presets import (
    PolicyMetadata,
    UnknownPresetError,
    list_presets,
    resolve_anonymization_options,
)
from app.core.report import write_anonymization_report
from app.core.schemas import AnonymizeMode, AnonymizeResponse
from app.document_io import (
    ensure_mapping_path_distinct,
    ensure_safe_mapping_path,
    ensure_safe_output_path,
    ensure_safe_report_path,
    read_document_file,
    write_text_file,
)
from app.security.encrypted_mapping import (
    DEFAULT_MAPPING_PASSPHRASE_ENV,
    write_encrypted_mapping_file,
)

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_UNSAFE = 2


def _parse_mode(value: str) -> AnonymizeMode:
    try:
        return AnonymizeMode(value)
    except ValueError as exc:
        raise InvalidAnonymizationMode(
            f"Invalid mode: {value!r}. Use 'replace', 'redact', or 'pseudonymize'."
        ) from exc


def _optional_bool_from_args(args: argparse.Namespace, name: str) -> bool | None:
    if not hasattr(args, name):
        return None
    value = getattr(args, name)
    return value if value is not None else None


def _anonymization_kwargs(args: argparse.Namespace) -> dict:
    from app.core.gliner_config import validate_gliner_labels

    preset_id = getattr(args, "preset", None)
    use_ner = _optional_bool_from_args(args, "use_ner")
    use_gliner = _optional_bool_from_args(args, "use_gliner")

    threshold_raw = getattr(args, "gliner_threshold", None)
    threshold: float | None = None
    if threshold_raw is not None:
        threshold = float(threshold_raw)
        if threshold < 0.0 or threshold > 1.0:
            raise MithrilVeilError("gliner-threshold must be between 0.0 and 1.0.")

    labels = getattr(args, "gliner_labels", None) or None
    if labels is not None:
        labels = validate_gliner_labels(labels)

    return resolve_anonymization_options(
        preset_id=preset_id,
        use_ner=use_ner,
        use_gliner=use_gliner,
        gliner_labels=labels,
        gliner_threshold=threshold,
        gliner_model_name=getattr(args, "gliner_model_name", None),
    )


def _add_batch_anonymize_args(parser: argparse.ArgumentParser) -> None:
    """Shared flags for anonymize-dir (no pseudonymize / mapping)."""
    parser.add_argument(
        "--mode",
        default="replace",
        choices=[m.value for m in AnonymizeMode],
        help="Anonymization mode (default: replace; batch supports replace/redact only)",
    )
    parser.add_argument(
        "--mapping-output",
        default=None,
        metavar="PATH",
        help="Not supported for batch (use anonymize-file with pseudonymize)",
    )
    parser.add_argument(
        "--preset",
        default=None,
        metavar="PRESET_ID",
        help="Policy preset (e.g. general_ru, legal_ru, valuation_ru)",
    )
    parser.add_argument(
        "--use-ner",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable local Natasha NER (overrides preset default)",
    )
    parser.add_argument(
        "--use-gliner",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable local GLiNER (overrides preset default)",
    )
    parser.add_argument(
        "--gliner-label",
        action="append",
        dest="gliner_labels",
        metavar="LABEL",
        help="GLiNER label (repeatable; default labels used if omitted)",
    )
    parser.add_argument(
        "--gliner-threshold",
        type=float,
        default=None,
        help="Minimum GLiNER score (0.0–1.0; preset or 0.5 default)",
    )
    parser.add_argument(
        "--gliner-model-name",
        default=None,
        help="Hugging Face GLiNER model id (default: urchade/gliner_mediumv2.1)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing sanitized outputs and batch report",
    )


def _add_common_anonymize_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--mode",
        default="replace",
        choices=[m.value for m in AnonymizeMode],
        help="Anonymization mode (default: replace)",
    )
    parser.add_argument(
        "--preset",
        default=None,
        metavar="PRESET_ID",
        help="Policy preset (e.g. general_ru, legal_ru, valuation_ru)",
    )
    parser.add_argument(
        "--use-ner",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable local Natasha NER (overrides preset default)",
    )
    parser.add_argument(
        "--use-gliner",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable/disable local GLiNER (overrides preset default)",
    )
    parser.add_argument(
        "--gliner-label",
        action="append",
        dest="gliner_labels",
        metavar="LABEL",
        help="GLiNER label (repeatable; default labels used if omitted)",
    )
    parser.add_argument(
        "--gliner-threshold",
        type=float,
        default=None,
        help="Minimum GLiNER score (0.0–1.0; preset or 0.5 default)",
    )
    parser.add_argument(
        "--gliner-model-name",
        default=None,
        help="Hugging Face GLiNER model id (default: urchade/gliner_mediumv2.1)",
    )
    parser.add_argument(
        "--mapping-output",
        default=None,
        metavar="PATH",
        help="Encrypted mapping file path (.json.enc; pseudonymize mode only)",
    )
    parser.add_argument(
        "--mapping-passphrase-env",
        default=DEFAULT_MAPPING_PASSPHRASE_ENV,
        metavar="ENV_VAR",
        help=(
            "Environment variable holding the mapping encryption passphrase "
            f"(default: {DEFAULT_MAPPING_PASSPHRASE_ENV})"
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output, report, or mapping files",
    )


def _validate_mapping_output_args(args: argparse.Namespace, mode: AnonymizeMode) -> None:
    if getattr(args, "mapping_output", None) and mode != AnonymizeMode.PSEUDONYMIZE:
        raise MithrilVeilError("--mapping-output is only supported when --mode is pseudonymize.")


def _pseudonymization_session(mode: AnonymizeMode) -> PseudonymizationSession | None:
    if mode == AnonymizeMode.PSEUDONYMIZE:
        return PseudonymizationSession.reversible()
    return None


def _write_mapping_output_if_requested(
    args: argparse.Namespace,
    session: PseudonymizationSession | None,
) -> None:
    mapping_output = getattr(args, "mapping_output", None)
    if not mapping_output:
        return
    if session is None or session.mapping is None:
        raise MithrilVeilError("Internal error: pseudonymize session has no mapping.")
    mapping_path = Path(mapping_output)
    force = bool(getattr(args, "force", False))
    ensure_safe_mapping_path(mapping_path, force=force)
    write_encrypted_mapping_file(
        mapping_path,
        session.mapping.serialize_for_encryption(),
        force=force,
        passphrase_env=getattr(args, "mapping_passphrase_env", DEFAULT_MAPPING_PASSPHRASE_ENV),
    )
    session.mark_mapping_written(encrypted=True)


def _run_anonymization_from_args(
    args: argparse.Namespace,
    text: str,
) -> tuple[AnonymizeResponse, PolicyMetadata | None, PseudonymizationSession | None]:
    mode = _parse_mode(args.mode)
    _validate_mapping_output_args(args, mode)
    if getattr(args, "mapping_output", None):
        ensure_safe_mapping_path(
            Path(args.mapping_output),
            force=bool(getattr(args, "force", False)),
        )
    resolved = _anonymization_kwargs(args)
    session = _pseudonymization_session(mode)
    response, policy = run_anonymization(text, mode, _resolved=resolved, session=session)
    _write_mapping_output_if_requested(args, session)
    return response, policy, session


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


def _cmd_list_presets(_args: argparse.Namespace) -> int:
    for info in list_presets():
        print(f"{info.id:<16}{info.name}")
    return EXIT_SUCCESS


def _cmd_anonymize_text(args: argparse.Namespace) -> int:
    if not args.text.strip():
        print("Error: --text must not be empty.", file=sys.stderr)
        return EXIT_ERROR
    response, _policy, _session = _run_anonymization_from_args(args, args.text)
    _print_stderr_summary(response)
    sys.stdout.write(response.text)
    return EXIT_SUCCESS


def _cmd_anonymize_stdin(args: argparse.Namespace) -> int:
    try:
        raw = sys.stdin.read()
    except OSError as exc:
        print(f"Error: cannot read stdin: {exc}", file=sys.stderr)
        return EXIT_ERROR
    if not raw.strip():
        print("Error: stdin input is empty.", file=sys.stderr)
        return EXIT_ERROR
    response, _policy, _session = _run_anonymization_from_args(args, raw)
    _print_stderr_summary(response)
    sys.stdout.write(response.text)
    return EXIT_SUCCESS


def _cmd_anonymize_file(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)
    force = bool(args.force)

    ensure_safe_output_path(input_path, output_path, force=force)
    if args.report:
        ensure_safe_report_path(Path(args.report), force=force)
    if getattr(args, "mapping_output", None):
        mapping_path = Path(args.mapping_output)
        ensure_safe_mapping_path(mapping_path, force=force)
        ensure_mapping_path_distinct(
            mapping_path,
            input_path=input_path,
            output_path=output_path,
            report_path=Path(args.report) if args.report else None,
        )

    try:
        content, source = read_document_file(input_path)
    except (
        UnsupportedDocumentType,
        EncryptedDocumentUnsupported,
        InputFileTooLarge,
        EmptyExtractedText,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_UNSAFE
    except MithrilVeilError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    response, policy, session = _run_anonymization_from_args(args, content)
    try:
        write_text_file(output_path, response.text, force=force)
    except UnsupportedDocumentType as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_UNSAFE

    if args.report:
        report_path = Path(args.report)
        try:
            write_anonymization_report(
                report_path,
                response,
                _parse_mode(args.mode),
                force=force,
                source=source,
                policy=policy,
                mapping_metadata=session.mapping_metadata if session else None,
            )
        except UnsafeFileOperation as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return EXIT_UNSAFE
        except MithrilVeilError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return EXIT_ERROR

    _print_stderr_summary(response)
    return EXIT_SUCCESS


def _cmd_anonymize_dir(args: argparse.Namespace) -> int:
    try:
        resolved = _anonymization_kwargs(args)
    except MithrilVeilError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return cmd_anonymize_dir(args, anonymization_kwargs=resolved)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mithril-veil",
        description="Self-hosted Russian PII anonymization for safer AI workflows.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version", help="Print version and exit")
    subparsers.add_parser("list-presets", help="List available policy presets")

    text_parser = subparsers.add_parser("anonymize-text", help="Anonymize inline text")
    text_parser.add_argument("--text", required=True, help="Input text to anonymize")
    _add_common_anonymize_args(text_parser)

    stdin_parser = subparsers.add_parser("anonymize-stdin", help="Anonymize text from stdin")
    _add_common_anonymize_args(stdin_parser)

    file_parser = subparsers.add_parser(
        "anonymize-file",
        help="Anonymize a text, markdown, DOCX, or text-based PDF file",
    )
    file_parser.add_argument(
        "--input",
        required=True,
        help="Input file path (.txt, .md, .docx, .pdf)",
    )
    file_parser.add_argument("--output", required=True, help="Output file path")
    _add_common_anonymize_args(file_parser)
    file_parser.add_argument("--report", help="Optional safe JSON report path")

    dir_parser = subparsers.add_parser(
        "anonymize-dir",
        help="Batch-anonymize supported files under a directory (replace/redact only)",
    )
    dir_parser.add_argument(
        "input_dir",
        help="Root directory to scan recursively for supported files",
    )
    dir_parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for sanitized .anonymized.txt outputs (mirrors relative paths)",
    )
    _add_batch_anonymize_args(dir_parser)
    dir_parser.add_argument(
        "--report",
        help="Optional aggregate safe JSON batch report path",
    )
    dir_parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop batch on the first file processing failure",
    )
    dir_parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="Include hidden files and directories (default: skip)",
    )
    dir_parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        metavar="N",
        help="Abort if more than N supported files are found",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "version": _cmd_version,
        "list-presets": _cmd_list_presets,
        "anonymize-text": _cmd_anonymize_text,
        "anonymize-stdin": _cmd_anonymize_stdin,
        "anonymize-file": _cmd_anonymize_file,
        "anonymize-dir": _cmd_anonymize_dir,
    }

    try:
        return handlers[args.command](args)
    except UnknownPresetError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except InvalidAnonymizationMode as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (
        UnsupportedDocumentType,
        EncryptedDocumentUnsupported,
        InputFileTooLarge,
        EmptyExtractedText,
        UnsafeFileOperation,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_UNSAFE
    except (
        MappingPassphraseMissing,
        InvalidEncryptedMappingPath,
    ) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except MithrilVeilError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
