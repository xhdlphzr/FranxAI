# Copyright (C) 2026 xhdlphzr
#
# This file is part of EasyMate.
#
# EasyMate is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
#
# EasyMate is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with EasyMate.  If not, see <https://www.gnu.org/licenses/>.

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

# 初始化列表：存储所有工具的元数据
tools_metadata = []
# 初始化字典：存储所有工具函数的映射
tool_functions = {}
# 初始化列表：存储所有工具的README内容
readmes = []

# 遍历工具目录中的所有子目录
for item in TOOLS_DIR.iterdir():
    # 跳过非目录项和以'__'开头的特殊目录
    if not item.is_dir() or item.name.startswith('__'):
        continue

    # 获取工具名称
    tool_name = item.name

    # 定义配置文件、工具文件和README文件的路径
    config_path = item / 'config.json'
    tool_path = item / 'tool.py'
    readme_path = item / 'README.md'

    # 检查工具模块是否包含所有必要文件
    if not (config_path.exists() and tool_path.exists() and readme_path.exists):
        print(f"⚠️ 工具 {tool_name} 缺少必要文件，跳过")
        continue

    try:
        # 读取配置文件
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"⚠️ 工具 {tool_name} 的 config.json 解析失败：{e}，跳过")
        continue

    # 检查配置文件格式是否正确
    if not isinstance(config, dict) or 'type' not in config or 'function' not in config:
        print(f"⚠️ 工具 {tool_name} 的 config.json 格式不正确（缺少 type 或 function），跳过")
        continue

    # 获取工具函数信息
    func_info = config['function']
    if 'name' not in func_info:
        print(f"⚠️ 工具 {tool_name} 的 config.json 中 function 缺少 name 字段，跳过")
        continue

    name = func_info['name']

    try:
        # 动态导入工具模块
        spec = importlib.util.spec_from_file_location(f"tools.{tool_name}", tool_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"tools.{tool_name}"] = module
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"⚠️ 工具 {tool_name} 的 tool.py 导入失败：{e}，跳过")
        continue

    # 检查工具模块是否定义了execute函数
    if not hasattr(module, 'execute'):
        print(f"⚠️ 工具 {tool_name} 的 tool.py 未定义 execute 函数，跳过")
        continue

    # 将工具元数据添加到列表
    tools_metadata.append(config)

    # 将工具函数添加到字典（通过函数名映射到execute函数）
    tool_functions[name] = module.execute

    # 读取并存储工具的README内容
    if readme_path.exists():
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read().strip()
                if readme_content:
                    readmes.append(readme_content)
        except Exception as e:
            print(f"⚠️ 工具 {tool_name} 的 README.md 读取失败：{e}")

# 将所有README内容合并为一个字符串
readmes_combined = "\n\n".join(readmes)

# 导出所有公共接口
__all__ = ['tools_metadata', 'tool_functions', 'readmes_combined']
