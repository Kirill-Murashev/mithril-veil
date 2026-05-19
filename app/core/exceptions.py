"""Project-specific exceptions for CLI and document I/O."""


class MithrilVeilError(Exception):
    """Base error for user-facing CLI and I/O failures."""


class UnsupportedDocumentType(MithrilVeilError):
    """Raised when a document format is not supported in the current slice."""


class UnsafeFileOperation(MithrilVeilError):
    """Raised when a file operation would overwrite input or existing output without --force."""


class InvalidAnonymizationMode(MithrilVeilError):
    """Raised when an anonymization mode is not recognized."""
