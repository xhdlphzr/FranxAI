# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAI.
# FranxAI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAI.  If not, see <https://www.gnu.org/licenses/>.

"""
工具系统初始化模块
自动加载所有可用的工具模块，生成元数据和工具函数
"""

import json
import importlib.util
import sys
from pathlib import Path

# 获取工具目录的绝对路径
TOOLS_DIR = Path(__file__).parent

# 存储所有内置工具的内部函数映射（工具名 -> execute 函数）
_internal_tools = {}
# 存储所有内置工具的 README 内容（用于系统提示）
readmes = []

# 遍历所有子目录
for item in TOOLS_DIR.iterdir():
    if not item.is_dir() or item.name.startswith('__'):
        continue
    
    tool_name = item.name
    tool_path = item / 'tool.py'
    readme_path = item / 'README.md'

    # 必要文件检查（不再需要 config.json）
    if not (tool_path.exists() and readme_path.exists()):
        print(f"⚠️ 工具 {tool_name} 缺少 tool.py 或 README.md，跳过")
        continue

    # 动态导入 tool.py
    try:
        spec = importlib.util.spec_from_file_location(f"tools.{tool_name}", tool_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"tools.{tool_name}"] = module
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"⚠️ 工具 {tool_name} 的 tool.py 导入失败：{e}，跳过")
        continue

    if not hasattr(module, 'execute'):
        print(f"⚠️ 工具 {tool_name} 的 tool.py 未定义 execute 函数，跳过")
        continue

    # 保存内部函数
    _internal_tools[tool_name] = module.execute

    # 读取 README
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read().strip()
            if readme_content:
                readmes.append(readme_content)
    except Exception as e:
        print(f"⚠️ 工具 {tool_name} 的 README.md 读取失败：{e}")

# 合并所有内置工具的 README
readmes_combined = "\n\n".join(readmes)

# 定义统一的 tools 函数
def tools(tool_name: str, arguments: dict = None) -> str:
    """
    统一调用接口，根据工具名分发到具体的内部工具函数。
    """
    if tool_name not in _internal_tools:
        return f"错误：未知工具 {tool_name}"

    if tool_name not in _internal_tools:
        return f"错误：未知工具 {tool_name}"
    try:
        return _internal_tools[tool_name](**(arguments or {}))
    except Exception as e:
        return f"调用失败: {e}"

# 导出工具函数字典（只有一个 tools 函数）
tool_functions = {"tools": tools}

# 构造统一工具的元数据（直接构造，不依赖外部 JSON）
tools_metadata = [
    {
        "type": "function",
        "function": {
            "name": "tools",
            "description": "调用任何可用工具。参数：tool_name (工具名), arguments (JSON 对象)。所有内置工具都通过此工具调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "工具名称，如 read、write、command、search、similarity、add_task、del_task、ett、beijing_subway 等"
                    },
                    "arguments": {
                        "type": "object",
                        "description": "工具参数"
                    }
                },
                "required": ["tool_name"]
            }
        }
    }
]

print("内置工具列表:", list(_internal_tools.keys()))
__all__ = ['tools_metadata', 'tool_functions', 'readmes_combined']