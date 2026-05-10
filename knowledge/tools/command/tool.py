"""
Execute System Command Tool
Allows AI to execute system commands, delete operations are prohibited for security
"""

import subprocess
import locale

# System encoding for decoding command output (e.g. cp936 on Chinese Windows)
_SYS_ENCODING = locale.getpreferredencoding()


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
        "rm ",
        "del ",
        "rmdir ",
        "rd ",
        "erase ",
        "shred ",
        "unlink ",
        "remove-item",
        "ri ",
        "rmdir /s",
        "rd /s",
        "remove-item -recurse",
        "rm -r",
        "rm -f",
        "rm -rf",
        " && rmdir",
        " && del",
        " | rmdir",
        " | del",
    ]

    # Check if it contains dangerous command patterns
    for pattern in dangerous_patterns:
        if pattern in cmd_lower:
            return (
                "❌ Error: Deletion commands are prohibited. FranxAgent security rules do not allow direct deletion of files or folders."
                "If you need to clean up files, please tell me to use 'move' operation, I will help you move files to 'C:\\ToBeDeleted' directory."
            )

    try:
        # Execute command, capture output and errors
        result = subprocess.run(command, shell=True, capture_output=True, timeout=30)

        # Decode with system encoding first (e.g. cp936 on Chinese Windows), fall back to UTF-8
        def safe_decode(data: bytes) -> str:
            for enc in (_SYS_ENCODING, "utf-8"):
                try:
                    return data.decode(enc)
                except (UnicodeDecodeError, LookupError):
                    continue
            return data.decode("utf-8", errors="replace")

        stdout = safe_decode(result.stdout)
        stderr = safe_decode(result.stderr)

        # Build output: stdout first, then stderr if present
        parts = []
        if stdout.strip():
            parts.append(stdout.strip())
        if stderr.strip():
            parts.append(f"[stderr]\n{stderr.strip()}")
        output = "\n".join(parts)

        if result.returncode != 0:
            prefix = f"Command returned non-zero exit code {result.returncode}"
            output = f"{prefix}\n{output}" if output else prefix

        return output or "Command executed successfully (no output)"

    except subprocess.TimeoutExpired:
        return "Error: Command execution timed out"
    except Exception as e:
        return f"Execution failed: {e}"
