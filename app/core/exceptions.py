"""Project-specific exceptions for CLI and document I/O."""


class MithrilVeilError(Exception):
    """Base error for user-facing CLI and I/O failures."""


class UnsupportedDocumentType(MithrilVeilError):
    """Raised when a document format is not supported."""


class UnsafeFileOperation(MithrilVeilError):
    """Raised when a file operation would overwrite input or existing output without --force."""


class InvalidAnonymizationMode(MithrilVeilError):
    """Raised when an anonymization mode is not recognized."""


class InputFileTooLarge(MithrilVeilError):
    """Raised when an input file exceeds the configured size limit."""


class EmptyExtractedText(MithrilVeilError):
    """Raised when a document yields no extractable text."""


class EncryptedDocumentUnsupported(UnsupportedDocumentType):
    """Raised when a document is encrypted and cannot be processed."""
