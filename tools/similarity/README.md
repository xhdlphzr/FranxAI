<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAI.
FranxAI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAI.  If not, see <https://www.gnu.org/licenses/>.
-->

### `similarity` — 检测字符串相似度

- **用途**
计算两个字符串在固定滑动窗口下的相似度（窗口大小固定为3字节，基于滚动哈希）。适用于文本局部重复检测、文件名比较等场景。

- **输入**
    ```json
    {
    "text1": "第一个字符串",
    "text2": "第二个字符串"
    }
    ```

    参数说明：
    - `text1`：**string**，必填，要比较的第一个字符串
    - `text2`：**string**，必填，要比较的第二个字符串

- **输出**
    返回一个字符串，格式为 `"XX.XX%"`，表示相似度百分比。如果任一字符串长度小于3字节，返回 `"0.00%"`。

- **注意事项**
    - 字符串按 UTF-8 编码的字节序列处理：英文字符占1字节，中文字符通常占3字节，窗口大小固定为3字节。
    - 比较的是窗口哈希值的集合，不关心窗口出现的顺序，只关注窗口内容是否相同。
    - 适合短文本比较，长文本仍可计算但可能无法捕捉长程模式。