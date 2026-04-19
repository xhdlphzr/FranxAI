# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Execute System Command Tool
Allows AI to execute system commands, delete operations are prohibited for security
"""

import subprocess

def execute(command: str) -> str:
    """
    Execute system command

    Args:
        command: Command string to execute

    Returns:
        Command execution result or error message
    """
    # Convert command to lowercase for security check
    cmd_lower = command.lower()

    # Define dangerous command pattern list
    dangerous_patterns = [
        "rm ", "del ", "rmdir ", "rd ", "erase ", "shred ", "unlink ",
        "remove-item", "ri ", "rmdir /s", "rd /s", "remove-item -recurse",
        "rm -r", "rm -f", "rm -rf",
        " && rmdir", " && del", " | rmdir", " | del"
    ]

    # Check if it contains dangerous command patterns
    for pattern in dangerous_patterns:
        if pattern in cmd_lower:
            return ("❌ Error: Deletion commands are prohibited. FranxAgent security rules do not allow direct deletion of files or folders."
                    "If you need to clean up files, please tell me to use 'move' operation, I will help you move files to 'C:\\ToBeDeleted' directory.")

    try:
        # Execute command, capture output and errors
        result = subprocess.run(f"{command}", shell=True, capture_output=True, timeout=30)
        stdout = result.stdout.decode('utf-8', errors='replace')
        stderr = result.stderr.decode('utf-8', errors='replace')
        output = stdout + stderr

        # If command returns non-zero exit code, add error message to output
        if result.returncode != 0:
            output = f"Command returned non-zero exit code {result.returncode}\n{output}"
        # If no output, return success message
        return output.strip() or "Command executed successfully (no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command execution timed out"
    except Exception as e:
        return f"Execution failed: {e}"
