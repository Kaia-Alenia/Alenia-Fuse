from dataclasses import dataclass, field
from pathlib import Path

from fuse.media.models import Media


@dataclass
class OperationResult:
    """Standardized return type for all API operations (§17)."""
    success: bool
    operation: str = ""
    input_path: Path | None = None
    output_path: Path | None = None
    media: Media | None = None
    elapsed_seconds: float = 0.0
    warnings: list[str] = field(default_factory=list)
    error: str | None = None

    @classmethod
    def from_success(
        cls,
        output_path: Path,
        operation: str = "",
        input_path: Path | None = None,
        elapsed_seconds: float = 0.0,
        warnings: list[str] | None = None,
        inspect_output: bool = True,
    ) -> "OperationResult":
        """
        Creates a successful result.
        Validates the output file exists, has size > 0, and inspects it via FFprobe.
        """
        if not output_path.exists():
            return cls(
                success=False,
                operation=operation,
                input_path=input_path,
                output_path=output_path,
                elapsed_seconds=elapsed_seconds,
                warnings=warnings or [],
                error="Output file not found.",
            )

        size = output_path.stat().st_size
        if size == 0:
            output_path.unlink(missing_ok=True)
            return cls(
                success=False,
                operation=operation,
                input_path=input_path,
                output_path=output_path,
                elapsed_seconds=elapsed_seconds,
                warnings=warnings or [],
                error="Output file is empty (0 bytes).",
            )

        if not inspect_output:
            return cls(
                success=True,
                operation=operation,
                input_path=input_path,
                output_path=output_path,
                elapsed_seconds=elapsed_seconds,
                warnings=warnings or [],
            )

        try:
            media = Media.inspect(str(output_path))
            return cls(
                success=True,
                operation=operation,
                input_path=input_path,
                output_path=output_path,
                media=media,
                elapsed_seconds=elapsed_seconds,
                warnings=warnings or [],
            )
        except Exception as e:
            return cls(
                success=False,
                operation=operation,
                input_path=input_path,
                output_path=output_path,
                elapsed_seconds=elapsed_seconds,
                warnings=warnings or [],
                error=f"Validation failed: {e}",
            )

    @classmethod
    def from_error(
        cls,
        error: str,
        operation: str = "",
        input_path: Path | None = None,
        output_path: Path | None = None,
        elapsed_seconds: float = 0.0,
        warnings: list[str] | None = None,
    ) -> "OperationResult":
        """Creates a failed result."""
        # Keep compatibility with the original helpers, which passed the
        # output path as the second positional argument.
        if isinstance(operation, Path) and input_path is None and output_path is None:
            output_path = operation
            operation = ""
        return cls(
            success=False,
            operation=operation,
            input_path=input_path,
            output_path=output_path,
            elapsed_seconds=elapsed_seconds,
            warnings=warnings or [],
            error=error,
        )
