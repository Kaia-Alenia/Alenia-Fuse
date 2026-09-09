import os
import sys
from pathlib import Path
from fuse.cli.registry import register_command, CommandArgument
from fuse.i18n.manager import t
from fuse.media.models import Media
from fuse.api.result import OperationResult
from fuse.cli.batch import get_auto_output_path, prompt_batch_formats
from fuse.cli.utils import (
    resolve_inputs, require_file, confirm_overwrite,
    build_progress_callback, finish_progress, friendly_error,
)
