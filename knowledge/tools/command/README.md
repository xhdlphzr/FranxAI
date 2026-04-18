<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### `command` - Execute System Commands (With Administrator Privileges)
- **Purpose**: Use this tool when users need to run programs, execute scripts, manage system services, install software, or perform other command-line tasks. This tool has **administrator privileges**, enabling most system-level operations.
- **Input**:
```json
{
    "command": "Full command string to execute"
}
```
- `command`: **string** (required; pass the complete system command string)
- **Output**: Standard output and standard error output of the command. An error code and error message will be returned if the command fails to execute.
- **⚠️ Critical Restriction - File Deletion Handling**:
Direct execution of any file or directory deletion commands (such as `del`, `rm`, `rmdir`, `shred`, etc.) with this tool is **strictly prohibited**. If the user requests file deletion, you must:
    1. **Do not use the `command` tool to perform deletion operations.**
    2. Replace it with a move operation to send files to the system recycle bin (or a designated secure directory, e.g., `C:\Users\Username\To-Delete`). Examples:
        - On Windows: Use `move <file path> <recycle bin path>`. For safe recycling via PowerShell: `Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile('<file>','OnlyErrorDialogs','SendToRecycleBin')`. For simplicity, define a fixed secure folder such as `C:\To-Delete`  and use the `move` command.
        - On Linux/macOS: Use commands like `mv <file> ~/.Trash/` or `gio trash <file>`.
    3. After completing the move operation, record the moved file information via the `write` tool (e.g., write to a log file) for user recovery later.
- **Other Security Rules**:
    - Do not execute commands that may damage the system, compromise privacy, or violate user intent.
    - Never run high-risk operations (e.g., disk formatting, registry modification) regardless of user consent.
    - Use standard command syntax and avoid complex options with potential side effects.

## 📘 Common Command Reference
Below is the purpose, cross-platform differences, and permission requirements for common system and development commands for decision-making. All commands must follow the above security rules, especially the ban on direct deletion.

### 1. File & Directory Operations

| Command (Win) | Command (macOS) | Purpose | Typical Usage | Permission Requirement |
|-----------|------------|------|---------|---------|
| `dir` | `ls` | List directory contents | `dir C:\path` / `ls -la /path` | Regular user |
| `cd` | `cd` | Change working directory | `cd C:\path` / `cd /path` | Regular user |
| `copy` | `cp` | Copy files or directories | `copy a.txt b.txt` / `cp a.txt b.txt` | Regular user |
| `move` | `mv` | Move or rename files/directories | `move a.txt b.txt` / `mv a.txt b.txt` | Regular user |
| `mkdir` | `mkdir` | Create new directories | `mkdir newfolder` / `mkdir newfolder` | Regular user (admin rights may apply to system-protected folders) |
| `rmdir` | `rmdir` | Delete empty directories | `rmdir emptydir` / `rmdir emptydir` | Regular user |
| `del` | `rm` | Delete files (Direct use prohibited) | `del file.txt` / `rm file.txt` | Regular user (Violates security rules) |
| - | `rm -r` | Recursively delete directories (Direct use prohibited) | `rm -r folder` | Regular user (Violates security rules) |
| `type` | `cat` | Display file content | `type file.txt` / `cat file.txt` | Regular user |
| `find` | `find` | Search for files | `find . -name "*.txt"` | Regular user |

### 2. System Information & Management

| Command (Win) | Command (Unix) | Purpose | Typical Usage | Permission Requirement |
|-----------|------------|------|---------|---------|
| `ver` | `uname -a` | View OS version | `ver` / `uname -a` | Regular user |
| `whoami` | `whoami` | Show current username | `whoami` | Regular user |
| `hostname` | `hostname` | Show device hostname | `hostname` | Regular user |
| `ipconfig` | `ifconfig` or `ip a` | Display network configuration | `ipconfig` / `ifconfig` | Regular user |
| `ping` | `ping` | Test network connectivity | `ping 8.8.8.8` | Regular user |
| `tasklist` | `ps aux` | List running processes | `tasklist` / `ps aux` | Regular user |
| `taskkill` | `kill` | Terminate processes | `taskkill /PID 1234` / `kill -9 1234` | Regular user (admin rights for certain processes) |
| `shutdown` | `shutdown` | Power off or restart | `shutdown /s` / `shutdown -h now` | **Administrator rights required** |
| `regedit` | - | Registry Editor (Windows) | Use with caution | **Administrator rights required** |

### 3. Package Managers

| Command (Win) | Command (Unix) | Purpose | Typical Usage | Permission Requirement |
|-----------|------------|------|---------|---------|
| `choco` | `apt` (Debian/Ubuntu) | Install/update software packages | `choco install git` / `apt install git` | **Administrator rights required** (`sudo` on Unix) |
| `winget` | `yum` (RHEL/CentOS) | Same as above | `winget install git` / `yum install git` | **Administrator rights required** |
| `scoop` | `brew` (macOS) | User-level package manager (No admin rights usually needed) | `scoop install git` / `brew install git` | Regular user |
| `pip` | `pip` | Python package manager | `pip install requests` | Regular user (Admin rights for global installs; virtual environments recommended) |
| `npm` | `npm` | Node.js package manager | `npm install express` | Regular user (Admin rights for global installs) |

### 4. Version Control

| Command | Purpose | Typical Usage | Permission Requirement |
|------|------|---------|---------|
| `git clone` | Clone remote repositories | `git clone https://github.com/...` | Regular user |
| `git add` | Add files to staging area | `git add .` | Regular user |
| `git commit` | Submit changes | `git commit -m "msg"` | Regular user |
| `git push` | Push updates to remote | `git push origin main` | Regular user |
| `git pull` | Pull remote updates | `git pull origin main` | Regular user |
| `git status` | Check workspace status | `git status` | Regular user |

### 5. Programming Languages & Compilers

| Command | Purpose | Typical Usage | Permission Requirement |
|------|------|---------|---------|
| `python` | Run Python scripts / Open interactive shell | `python script.py` | Regular user |
| `pip` | See package manager section | - | - |
| `g++` | Compile C++ programs | `g++ main.cpp -o app` | Regular user |
| `gcc` | Compile C programs | `gcc main.c -o app` | Regular user |
| `java` | Run Java programs | `java MainClass` | Regular user |
| `javac` | Compile Java programs | `javac Main.java` | Regular user |
| `node` | Run JavaScript programs | `node app.js` | Regular user |
| `make` | Execute Makefile builds | `make` | Regular user |

### 6. Network Tools

| Command | Purpose | Typical Usage | Permission Requirement |
|------|------|---------|---------|
| `curl` | Send HTTP requests | `curl https://api.example.com` | Regular user |
| `wget` | Download files | `wget https://example.com/file.zip` | Regular user |
| `netstat` | Show network connections | `netstat -an` | Regular user (Admin rights for certain details) |
| `ssh` | Remote login | `ssh user@host` | Regular user |
| `scp` | Remote file transfer | `scp file user@host:/path` | Regular user |

### 7. Other Common Tools

| Command | Purpose | Typical Usage | Permission Requirement |
|------|------|---------|---------|
| `echo` | Print text output | `echo Hello` | Regular user |
| `date` | View/set system date | `date` | Regular user (Admin rights to modify date) |
| `time` | Measure command execution time | `time ls` | Regular user |
| `sleep` | Pause execution for seconds | `sleep 5` | Regular user |
| `alias` | Create command aliases | `alias ll='ls -la'` | Regular user |
| `which` | Locate command file paths | `which python` | Regular user |

### 8. Special Warning for Dangerous Commands
- Disk formatting: `format` (Win) / `mkfs` (Unix) - **Requires explicit user authorization; extremely high risk (admin rights mandatory)**.
- Permission modification: `chmod` (Unix) - May affect system security; use cautiously.
- Ownership modification: `chown` (Unix) - Admin rights usually required.
- Registry modification: `reg` (Win) - May corrupt the system; use cautiously.

**Usage Principle**: Prioritize safe, compliant commands for user requests. Confirm permissions and risks with users if uncertain. Replace all deletion actions with file moves and record logs strictly.