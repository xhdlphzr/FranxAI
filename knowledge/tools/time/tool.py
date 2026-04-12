# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
Get Time Tool | 获取时间工具
Returns the current local date and time | 返回当前的本地日期和时间
"""

from datetime import datetime

def execute() -> str:
    """
    Get current date and time | 获取当前日期和时间

    Returns:
        Formatted datetime string, e.g., "2024-01-15 Wednesday 15:30:45" | 格式化的日期时间字符串，例如 "2024-01-15 星期三 15:30:45"
    """
    now = datetime.now()

    # List of weekday names | 星期名称列表
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    # Get the day of the week (0=Monday, 6=Sunday) | 获取星期几（0=星期一，6=星期日）
    weekday = weekdays[now.weekday()]

    # Return formatted string | 返回格式化字符串
    return now.strftime(f"%Y-%m-%d {weekday} %H:%M:%S")