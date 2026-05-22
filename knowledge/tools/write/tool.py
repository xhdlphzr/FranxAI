# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Write Tool - Proposal Mode

The write tool no longer performs any file operations on disk. Instead, it
computes the final file content that would result from applying the AI's
suggested changes, and returns this complete file content as a proposal string.

The frontend displays this content in a code review panel where the user can
inspect the diff, edit the code, and then approve the changes. Upon approval,
the frontend writes the file and returns the final content back to the AI so
it can continue the conversation with the latest file state.
"""

from pathlib import Path


def execute(path: str, content: str, mode="overwrite", start_line=0, end_line=0) -> str:
    """
    Compute and return the complete file content after applying the AI's changes.

    This function does NOT write to disk. It reads the original file (if it
    exists), applies the requested modification, and returns the resulting
    complete file content as a plain string.

    @param path: Full path of the target file.
    @param content: The content to be written/inserted/replaced.
    @param mode: Write mode --- "overwrite", "append", or "edit".
    @param start_line: Start line number for edit mode (1-based, inclusive).
    @param end_line: End line number for edit mode (1-based, inclusive).
    @returns: The complete file content after applying the requested change.
    """
    file_path = Path(path).expanduser().resolve()

    # Read original file content (empty string if file does not exist)
    try:
        original_content = file_path.read_text(encoding="utf-8")
        original_lines = original_content.split("\n")
    except (FileNotFoundError, PermissionError):
        original_content = ""
        original_lines = []

    if mode == "overwrite":
        # Replace entire file content
        return content

    elif mode == "append":
        # Append content to the end of the file
        if original_content and not original_content.endswith("\n"):
            return original_content + "\n" + content
        return original_content + content

    elif mode == "edit":
        # Replace lines start_line through end_line with new content
        if not original_content:
            # Editing an empty file: just return the content as the new file
            return content

        total_lines = len(original_lines)

        # Clamp line numbers to valid range
        start = max(1, start_line)
        end = min(end_line, total_lines) if end_line > 0 else total_lines

        if start > total_lines:
            # start_line beyond file end: append after a blank line
            return original_content + "\n" + content

        # Convert to 0-based indices
        start_idx = start - 1
        end_idx = end  # slicing is exclusive on the upper bound

        # Build the new file content
        new_lines = (
            original_lines[:start_idx] + content.split("\n") + original_lines[end_idx:]
        )
        return "\n".join(new_lines)

    else:
        # Unknown mode, return content unchanged
        return content
