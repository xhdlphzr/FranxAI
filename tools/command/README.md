<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAI.
FranxAI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAI.  If not, see <https://www.gnu.org/licenses/>.
-->

### `command` — 执行系统命令（具有管理员权限）
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