<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### `command` — 执行系统命令（拥有管理员权限）
- **用途**：当用户需要运行程序、执行脚本、管理系统服务、安装软件或执行其他命令行任务时使用此工具。此工具拥有**管理员权限**，可执行大多数系统级操作。
- **输入**：
```json
{
    "command": "要执行的完整命令字符串"
}
```
- `command`：**字符串**（必填；传入完整的系统命令字符串）
- **输出**：命令的标准输出和标准错误输出。如果命令执行失败，将返回错误码和错误信息。
- **⚠️ 关键限制 — 文件删除处理**：
使用此工具直接执行任何文件或目录删除命令（如 `del`、`rm`、`rmdir`、`shred` 等）是**严格禁止的**。如果用户请求删除文件，你必须：
    1. **不要使用 `command` 工具执行删除操作。**
    2. 替换为移动操作，将文件发送到系统回收站（或指定的安全目录，例如 `C:\Users\Username\To-Delete`）。示例：
        - Windows 上：使用 `move <文件路径> <回收站路径>`。通过 PowerShell 安全回收：`Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile('<文件>','OnlyErrorDialogs','SendToRecycleBin')`。为简便起见，可以定义一个固定的安全文件夹，如 `C:\To-Delete`，然后使用 `move` 命令。
        - Linux/macOS 上：使用 `mv <文件> ~/.Trash/` 或 `gio trash <文件>` 等命令。
    3. 完成移动操作后，通过 `write` 工具记录被移动文件的信息（例如写入日志文件），以便用户日后恢复。
- **其他安全规则**：
    - 不要执行可能损害系统、侵犯隐私或违背用户意图的命令。
    - 无论用户是否同意，绝不运行高风险操作（如磁盘格式化、注册表修改）。
    - 使用标准命令语法，避免具有潜在副作用的复杂选项。

## 📘 常用命令参考
以下是常见系统和开发命令的用途、跨平台差异及权限要求，供决策参考。所有命令必须遵循上述安全规则，尤其是禁止直接删除。

### 1. 文件与目录操作

| 命令 (Win) | 命令 (macOS) | 用途 | 典型用法 | 权限要求 |
|-----------|------------|------|---------|---------|
| `dir` | `ls` | 列出目录内容 | `dir C:\path` / `ls -la /path` | 普通用户 |
| `cd` | `cd` | 切换工作目录 | `cd C:\path` / `cd /path` | 普通用户 |
| `copy` | `cp` | 复制文件或目录 | `copy a.txt b.txt` / `cp a.txt b.txt` | 普通用户 |
| `move` | `mv` | 移动或重命名文件/目录 | `move a.txt b.txt` / `mv a.txt b.txt` | 普通用户 |
| `mkdir` | `mkdir` | 创建新目录 | `mkdir newfolder` / `mkdir newfolder` | 普通用户（系统保护文件夹可能需要管理员权限） |
| `rmdir` | `rmdir` | 删除空目录 | `rmdir emptydir` / `rmdir emptydir` | 普通用户 |
| `del` | `rm` | 删除文件（禁止直接使用） | `del file.txt` / `rm file.txt` | 普通用户（违反安全规则） |
| - | `rm -r` | 递归删除目录（禁止直接使用） | `rm -r folder` | 普通用户（违反安全规则） |
| `type` | `cat` | 显示文件内容 | `type file.txt` / `cat file.txt` | 普通用户 |
| `find` | `find` | 搜索文件 | `find . -name "*.txt"` | 普通用户 |

### 2. 系统信息与管理

| 命令 (Win) | 命令 (Unix) | 用途 | 典型用法 | 权限要求 |
|-----------|------------|------|---------|---------|
| `ver` | `uname -a` | 查看操作系统版本 | `ver` / `uname -a` | 普通用户 |
| `whoami` | `whoami` | 显示当前用户名 | `whoami` | 普通用户 |
| `hostname` | `hostname` | 显示设备主机名 | `hostname` | 普通用户 |
| `ipconfig` | `ifconfig` 或 `ip a` | 显示网络配置 | `ipconfig` / `ifconfig` | 普通用户 |
| `ping` | `ping` | 测试网络连通性 | `ping 8.8.8.8` | 普通用户 |
| `tasklist` | `ps aux` | 列出运行中的进程 | `tasklist` / `ps aux` | 普通用户 |
| `taskkill` | `kill` | 终止进程 | `taskkill /PID 1234` / `kill -9 1234` | 普通用户（某些进程需要管理员权限） |
| `shutdown` | `shutdown` | 关机或重启 | `shutdown /s` / `shutdown -h now` | **需要管理员权限** |
| `regedit` | - | 注册表编辑器（Windows） | 谨慎使用 | **需要管理员权限** |

### 3. 包管理器

| 命令 (Win) | 命令 (Unix) | 用途 | 典型用法 | 权限要求 |
|-----------|------------|------|---------|---------|
| `choco` | `apt` (Debian/Ubuntu) | 安装/更新软件包 | `choco install git` / `apt install git` | **需要管理员权限**（Unix 上需 `sudo`） |
| `winget` | `yum` (RHEL/CentOS) | 同上 | `winget install git` / `yum install git` | **需要管理员权限** |
| `scoop` | `brew` (macOS) | 用户级包管理器（通常无需管理员权限） | `scoop install git` / `brew install git` | 普通用户 |
| `pip` | `pip` | Python 包管理器 | `pip install requests` | 普通用户（全局安装需管理员权限；推荐使用虚拟环境） |
| `npm` | `npm` | Node.js 包管理器 | `npm install express` | 普通用户（全局安装需管理员权限） |

### 4. 版本控制

| 命令 | 用途 | 典型用法 | 权限要求 |
|------|------|---------|---------|
| `git clone` | 克隆远程仓库 | `git clone https://github.com/...` | 普通用户 |
| `git add` | 将文件添加到暂存区 | `git add .` | 普通用户 |
| `git commit` | 提交更改 | `git commit -m "msg"` | 普通用户 |
| `git push` | 推送更新到远程 | `git push origin main` | 普通用户 |
| `git pull` | 拉取远程更新 | `git pull origin main` | 普通用户 |
| `git status` | 查看工作区状态 | `git status` | 普通用户 |

### 5. 编程语言与编译器

| 命令 | 用途 | 典型用法 | 权限要求 |
|------|------|---------|---------|
| `python` | 运行 Python 脚本 / 打开交互式 shell | `python script.py` | 普通用户 |
| `pip` | 见包管理器部分 | - | - |
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
| `netstat` | 显示网络连接 | `netstat -an` | 普通用户（某些详情需管理员权限） |
| `ssh` | 远程登录 | `ssh user@host` | 普通用户 |
| `scp` | 远程文件传输 | `scp file user@host:/path` | 普通用户 |

### 7. 其他常用工具

| 命令 | 用途 | 典型用法 | 权限要求 |
|------|------|---------|---------|
| `echo` | 输出文本 | `echo Hello` | 普通用户 |
| `date` | 查看/设置系统日期 | `date` | 普通用户（修改日期需管理员权限） |
| `time` | 测量命令执行时间 | `time ls` | 普通用户 |
| `sleep` | 暂停执行若干秒 | `sleep 5` | 普通用户 |
| `alias` | 创建命令别名 | `alias ll='ls -la'` | 普通用户 |
| `which` | 定位命令文件路径 | `which python` | 普通用户 |

### 8. 危险命令特别警告
- 磁盘格式化：`format` (Win) / `mkfs` (Unix) — **需要用户明确授权；风险极高（必须管理员权限）**。
- 权限修改：`chmod` (Unix) — 可能影响系统安全，谨慎使用。
- 所有权修改：`chown` (Unix) — 通常需要管理员权限。
- 注册表修改：`reg` (Win) — 可能损坏系统，谨慎使用。

**使用原则**：优先使用安全、合规的命令完成用户请求。如不确定，向用户确认权限和风险。所有删除操作一律替换为文件移动，并严格记录日志。