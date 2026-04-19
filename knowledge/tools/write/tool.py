# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
File Write Tool
Allows the AI to write, append, or edit content in a specified file
"""

from pathlib import Path

def execute(path: str, content: str, mode="overwrite", start_line=0, end_line=0) -> str:
    """
    Write, append, or edit content in a file

    Args:
        path: Full path of the file
        content: Content to be written
        mode: Write mode - "overwrite", "append", or "edit"
        start_line: Start line number for edit mode (1-based, inclusive)
        end_line: End line number for edit mode (1-based, inclusive)

    Returns:
        Operation result information
    """
    try:
        # Resolve the path and handle user directory symbol (~)
        p = Path(path).expanduser().resolve()

        # Ensure the parent directory exists
        p.parent.mkdir(parents=True, exist_ok=True)

        if mode == "edit":
            # Edit mode: replace lines from start_line to end_line (1-based, inclusive)
            if start_line < 1:
                return "Edit failed: start_line must be >= 1"
            if end_line < start_line:
                return "Edit failed: end_line must be >= start_line"

            if not p.exists():
                return f"Edit failed: File does not exist - {p}"

            with open(p, 'r', encoding='utf-8') as f:
                original = f.read()

            lines = original.split('\n')
            total_lines = len(lines)

            if start_line > total_lines:
                return f"Edit failed: start_line ({start_line}) exceeds total lines ({total_lines})"

            # Clamp end_line to file length
            effective_end = min(end_line, total_lines)

            # Replace lines [start_line, end_line] with content
            # Empty content deletes the line range
            new_lines = content.split('\n') if content else []
            lines[start_line - 1:effective_end] = new_lines

            with open(p, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            return f"Successfully edited file: {p} (L{start_line}-L{effective_end} replaced)"
        else:
            # Select file opening mode based on the parameter
            flag = 'a' if mode == 'append' else 'w'

            # Write content to the file
            with open(p, flag, encoding='utf-8') as f:
                f.write(content)

            # Return success message
            return f"Successfully {'appended to' if mode=='append' else 'wrote to'} file: {p}"
    except Exception as e:
        return f"Write failed: {e}"