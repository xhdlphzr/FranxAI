<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### `command` - Execute System Commands (With Administrator Privileges) | 执行系统命令（具有管理员权限）
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
  - On Windows: Use `move <file path> <recycle bin path>`. For safe recycling via PowerShell: `Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile('<file>','OnlyErrorDialogs','SendToRecycleBin')`. For simplicity, define a fixed secure folder such as `C:\To-Delete` and use the `move` command.
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

- **用途**：当用户需要运行程序、执行脚本、管理系统服务、安装软件等需要命令行操作的任务时，使用此工具。此工具拥有**管理员权限**，因此可以执行大多数系统级操作。
- **输入**：
  ```json
  {
    "command": "要执行的完整命令字符串"
  }
  ```
  - `command`：**string**（必填，需传入完整的系统命令字符串）
- **输出**：命令的标准输出和标准错误输出。如果命令执行失败，会返回错误码和错误信息。
- **⚠️ 重要限制 — 删除文件处理**：
  此工具**严禁直接执行任何删除文件或目录的命令**（如 `del`、`rm`、`rmdir`、`shred` 等）。如果用户要求删除文件，你必须：
  1. **不要使用 `command` 工具执行删除操作。**
  2. 改为使用**移动操作**，将文件移动到系统的回收站（或一个指定的安全目录，如 `C:\Users\用户名\待删除`）。例如：
     - 在 Windows 上：使用 `move <文件路径> <回收站路径>` 或 PowerShell 的 `Remove-Item -LiteralPath <文件> -Force` ？不，Remove-Item 会直接删除。更安全的是移动到回收站：你可以使用 PowerShell 命令 `Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile('<文件>','OnlyErrorDialogs','SendToRecycleBin')`，但需要谨慎。简单起见，可以定义一个固定的安全目录，例如 `C:\待删除`，然后用 `move` 命令移过去。
     - 在 Linux/macOS 上：可以使用 `mv <文件> ~/.Trash/` 或 `gio trash <文件>` 等命令。
  3. 执行移动操作后，请务必通过 `write` 工具记录下被移动的文件信息（例如写入日志文件），以便用户日后找回。
- **其他安全规则**：
  - 不要执行任何可能损坏系统、危害隐私或违反用户意图的命令。
  - 在执行高危操作（如格式化磁盘、修改注册表等）之前，无论有没有用户同意，都不可以执行。
  - 尽量使用命令的标准语法，避免使用过于复杂或可能产生副作用的选项。

## 📘 常用命令参考

以下列出常见系统命令和开发工具命令的用途、跨平台差异及权限要求，供你决策时参考。**所有命令的执行均需遵守上述安全规则，尤其是禁止直接删除的禁令。**

### 1. 文件和目录操作

| 命令 (Win) | 命令 (macOS) | 用途 | 典型用法 | 权限要求 |
|-----------|------------|------|---------|---------|
| `dir` | `ls` | 列出目录内容 | `dir C:\path` / `ls -la /path` | 普通用户 |
| `cd` | `cd` | 切换工作目录 | `cd C:\path` / `cd /path` | 普通用户 |
| `copy` | `cp` | 复制文件或目录 | `copy a.txt b.txt` / `cp a.txt b.txt` | 普通用户 |
| `move` | `mv` | 移动文件或目录（也用于重命名） | `move a.txt b.txt` / `mv a.txt b.txt` | 普通用户 |
| `mkdir` | `mkdir` | 创建新目录 | `mkdir newfolder` / `mkdir newfolder` | 普通用户（在系统保护目录可能需要管理员） |
| `rmdir` | `rmdir` | 删除空目录 | `rmdir emptydir` / `rmdir emptydir` | 普通用户 |
| `del` | `rm` | **删除文件（禁止直接使用）** | `del file.txt` / `rm file.txt` | 普通用户（但违反安全规则） |
| - | `rm -r` | **递归删除目录（禁止直接使用）** | `rm -r folder` | 普通用户（但违反安全规则） |
| `type` | `cat` | 显示文件内容 | `type file.txt` / `cat file.txt` | 普通用户 |
| `find` | `find` | 搜索文件 | `find . -name "*.txt"` | 普通用户 |

### 2. 系统信息和管理

| 命令 (Win) | 命令 (Unix) | 用途 | 典型用法 | 权限要求 |
|-----------|------------|------|---------|---------|
| `ver` | `uname -a` | 查看操作系统版本 | `ver` / `uname -a` | 普通用户 |
| `whoami` | `whoami` | 显示当前用户名 | `whoami` | 普通用户 |
| `hostname` | `hostname` | 显示主机名 | `hostname` | 普通用户 |
| `ipconfig` | `ifconfig` 或 `ip a` | 显示网络配置 | `ipconfig` / `ifconfig` | 普通用户 |
| `ping` | `ping` | 测试网络连通性 | `ping 8.8.8.8` | 普通用户 |
| `tasklist` | `ps aux` | 列出运行进程 | `tasklist` / `ps aux` | 普通用户 |
| `taskkill` | `kill` | 终止进程 | `taskkill /PID 1234` / `kill -9 1234` | 普通用户（某些进程可能需要管理员） |
| `shutdown` | `shutdown` | 关机或重启 | `shutdown /s` / `shutdown -h now` | **需要管理员权限** |
| `regedit` | - | 注册表编辑器（Windows） | 谨慎使用 | **需要管理员权限** |

### 3. 包管理器

| 命令 (Win) | 命令 (Unix) | 用途 | 典型用法 | 权限要求 |
|-----------|------------|------|---------|---------|
| `choco` | `apt` (Debian/Ubuntu) | 安装/更新软件包 | `choco install git` / `apt install git` | **需要管理员权限**（Unix 下可能需要 `sudo`） |
| `winget` | `yum` (RHEL/CentOS) | 同上 | `winget install git` / `yum install git` | **需要管理员权限** |
| `scoop` | `brew` (macOS) | 用户级包管理器（通常不需管理员） | `scoop install git` / `brew install git` | 普通用户 |
| `pip` | `pip` | Python 包管理器 | `pip install requests` | 普通用户（全局安装可能需要管理员，建议使用虚拟环境） |
| `npm` | `npm` | Node.js 包管理器 | `npm install express` | 普通用户（全局安装可能需要管理员） |

### 4. 版本控制

| 命令 | 用途 | 典型用法 | 权限要求 |
|------|------|---------|---------|
| `git clone` | 克隆远程仓库 | `git clone https://github.com/...` | 普通用户 |
| `git add` | 添加文件到暂存区 | `git add .` | 普通用户 |
| `git commit` | 提交更改 | `git commit -m "msg"` | 普通用户 |
| `git push` | 推送至远程仓库 | `git push origin main` | 普通用户 |
| `git pull` | 拉取远程更新 | `git pull origin main` | 普通用户 |
| `git status` | 查看工作区状态 | `git status` | 普通用户 |

### 5. 编程语言和编译器

| 命令 | 用途 | 典型用法 | 权限要求 |
|------|------|---------|---------|
| `python` | 运行 Python 脚本/进入交互环境 | `python script.py` | 普通用户 |
| `pip` | 见包管理器 | - | - |
| `g++` | 编译 C++ 程序 | `g++ main.cpp -o app` | 普通用户 |
| `gcc` | 编译 C 程序 | `gcc main.c -o app` | 普通用户 |
| `java` | 运行 Java 程序 | `java MainClass` | 普通用户 |
| `javac` | 编译 Java 程序 | `javac Main.java` | 普通用户 |
| `node` | 运行 JavaScript 程序 | `node app.js` | 普通用户 |
| `make` | 执行 Makefile 构建 | `make` | 普通用户 |

### 6. 网络工具

| 命令 | 用途 | 典型用法 | 权限要求 |
|------|------|---------|---------|
| `curl` | 发送 HTTP 请求 | `curl https://api.example.com` | 普通用户 |
| `wget` | 下载文件 | `wget https://example.com/file.zip` | 普通用户 |
| `netstat` | 显示网络连接 | `netstat -an` | 普通用户（某些信息可能需要管理员） |
| `ssh` | 远程登录 | `ssh user@host` | 普通用户 |
| `scp` | 远程复制文件 | `scp file user@host:/path` | 普通用户 |

### 7. 其他常用工具

| 命令 | 用途 | 典型用法 | 权限要求 |
|------|------|---------|---------|
| `echo` | 输出文本 | `echo Hello` | 普通用户 |
| `date` | 显示/设置日期 | `date` | 普通用户（设置日期可能需要管理员） |
| `time` | 测量命令执行时间 | `time ls` | 普通用户 |
| `sleep` | 暂停指定秒数 | `sleep 5` | 普通用户 |
| `alias` | 创建命令别名 | `alias ll='ls -la'` | 普通用户 |
| `which` | 定位命令路径 | `which python` | 普通用户 |

### 8. 危险命令特别提示

- **格式化磁盘**：`format` (Win) / `mkfs` (Unix) — **必须获得用户明确授权，通常需要管理员权限，极危险。**
- **修改权限**：`chmod` (Unix) — 可能影响系统安全，谨慎使用。
- **修改所有者**：`chown` (Unix) — 通常需要管理员权限。
- **修改注册表**：`reg` (Win) — 可能破坏系统，谨慎使用。

**使用原则**：当用户需求涉及上述命令时，优先选择安全且符合意图的选项。若不确定命令的权限或潜在影响，先向用户确认。对于任何删除类操作，坚决采用移动替代方案，并记录日志。