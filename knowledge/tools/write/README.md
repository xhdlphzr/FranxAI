<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### `write` — Propose file content changes (proposal-review-overwrite mode)
- **Purpose**: Used when the AI wants to create a new file, write content to an existing file, or modify a file. The write tool **no longer performs any file operations**. Instead, it returns the AI's suggested complete file content as a string. The frontend displays this in a code review panel where the user can inspect diffs, edit the code, and approve the changes.
- **Input**:
    ```json
    {
        "path": "Full path of the file",
        "content": "Complete file content after modifications",
        "mode": "overwrite" or "append" or "edit",
        "start_line": 0,
        "end_line": 0
    }
    ```
    - `path`: **string**, required, full path of the target file.
    - `content`: **string**, required, the AI's suggested complete file content after all modifications. The frontend will diff this against the current file on disk.
    - `mode`: **string**, optional, default is "overwrite". Available values:
        - `"overwrite"`: Replace entire file
        - `"append"`: Append to end of file
        - `"edit"`: Replace lines from `start_line` to `end_line` (both inclusive, 1-based). Use with `read` tool's line numbers for precise editing.
    - `start_line`: **integer**, required in edit mode. Start line number (1-based, inclusive).
    - `end_line`: **integer**, required in edit mode. End line number (1-based, inclusive).
- **Output**: The AI's suggested complete file content as a plain string (not a dictionary).
- **Workflow**:
    1. The AI calls the `write` tool with the proposed file content.
    2. The backend returns the content string to the frontend without touching the disk.
    3. The frontend opens a code review panel showing the diff between the original file and the AI's proposal.
    4. The user can switch to edit mode, modify the code, then approve the changes.
    5. On approval, the frontend writes the file and sends the final content back to the AI so it stays in sync.
- **Notes**:
    - This tool does NOT execute any file operations. All disk writes are performed by the frontend after user approval.
    - In edit mode, always use `read` first to get the current line numbers, then specify the exact range to replace.
    - **Critical Rule for `edit` mode — Line Number Adherence (READ ONLY, NEVER PREDICT)**:
        - **ALL `start_line` and `end_line` values MUST come exclusively from the most recent `read` operation.** You are FORBIDDEN from predicting, calculating, or inferring line numbers based on the content of the edit itself.
        - **Original file only:** When deleting or replacing lines, use the line numbers of the ORIGINAL file BEFORE your edit. Example: If `read` shows lines 50-60 and you are replacing lines 54-57 with a 6-line block, you MUST use `start_line=54, end_line=57`. Using `54-59` (post-edit calculation) is a serious violation.
        - **No "drift" correction:** Do NOT try to adjust line numbers to compensate for how the edit will shift subsequent lines. That shift is handled internally; your job is to provide the exact current coordinates.
        - **Check your work:** Before calling `write` with `edit` mode, explicitly state in your plan: "I am replacing lines X to Y as they appear in the most recent `read` operation."