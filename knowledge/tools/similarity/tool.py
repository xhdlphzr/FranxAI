# Copyright (C) 2026 xhdlphzr, zhiziwj
# This file is part of FranxAI.
# FranxAI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAI.  If not, see <https://www.gnu.org/licenses/>.

"""
String Similarity Calculation Tool | 字符串相似度计算工具
Calculate the similarity of two strings using the rolling hash algorithm (window size 3 bytes) | 使用滚动哈希算法计算两个字符串的相似度（窗口大小为3字节）
"""

def execute(text1: str, text2: str) -> str:
    """
    Calculate the similarity of two strings | 计算两个字符串的相似度

    Args:
        text1: The first string | 第一个字符串
        text2: The second string | 第二个字符串

    Returns:
        Similarity percentage in the format "XX.XX%" | 相似度百分比，格式为 "XX.XX%"
    """
    # Base number and window size | 基数和窗口大小
    base = 131
    window_size = 3

    def rolling_hashes(s: str, w: int):
        """
        Calculate the rolling hash value set of a string | 计算字符串的滚动哈希值集合

        Args:
            s: Input string | 输入字符串
            w: Window size | 窗口大小

        Returns:
            List of hash values | 哈希值列表
        """
        if len(s) < w:
            return []
        h = 0
        p = 1
        # Precompute base to the power of w | 预计算base的w次方
        for i in range(w):
            p *= base
        res = []
        for i, ch in enumerate(s):
            # Update the hash value | 更新哈希值
            h = h * base + ord(ch)
            if i >= w:
                # Remove the contribution of characters outside the window | 移除窗口外的字符贡献
                h -= ord(s[i - w]) * p
            if i >= w - 1:
                # Record the window hash value | 记录窗口哈希值
                res.append(h)
        return res

    # Calculate the hash value sets of the two strings | 计算两个字符串的哈希值集合
    v1 = rolling_hashes(text1, window_size)
    v2 = rolling_hashes(text2, window_size)

    # If the length of either string is less than the window size, return 0% | 如果任一字符串长度小于窗口大小，返回0%
    if not v1 or not v2:
        return "0.00%"

    # Convert to sets and calculate common hash values | 转换为集合，计算公共哈希值
    set1 = set(v1)
    set2 = set(v2)
    common = set1 & set2
    same = len(common)

    # Calculate similarity: 2 * common elements / total number of elements | 计算相似度：2 * 公共元素 / 总元素数
    total = len(v1) + len(v2)
    similarity = 2.0 * same / total if total > 0 else 0.0

    # Return percentage | 返回百分比
    return f"{similarity*100:.2f}%"