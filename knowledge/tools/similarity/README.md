<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAgent.
FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.
-->

### `similarity` - Detect String Similarity | 检测字符串相似度
- **Purpose**
Calculate the similarity between two strings under a fixed sliding window (fixed window size: 3 bytes, based on rolling hash). Suitable for scenarios such as local text duplicate detection and filename comparison.

- **Input**
```json
{
"text1": "First string",
"text2": "Second string"
}
```

Parameter Description:
- `text1`: **string**, required, the first string to be compared
- `text2`: **string**, required, the second string to be compared

- **Output**
Returns a string in the format `"XX.XX%"`, representing the similarity percentage. If the length of either string is less than 3 bytes, it returns `"0.00%"`.

- **Notes**
- Strings are processed as UTF-8 encoded byte sequences: English characters occupy 1 byte, Chinese characters usually occupy 3 bytes, and the window size is fixed at 3 bytes.
- The comparison is based on sets of window hash values; the order of windows is ignored, only the consistency of window content matters.
- Suitable for short text comparison. It can still calculate results for long texts, but may fail to capture long-range patterns.
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