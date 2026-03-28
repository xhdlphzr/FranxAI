<!--
Copyright (C) 2026 xhdlphzr
This file is part of FranxAI.
FranxAI is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
FranxAI is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with FranxAI.  If not, see <https://www.gnu.org/licenses/>.
-->

### ett — 多模态理解（Everything to Text）

- **用途**：使用智谱 GLM-4.6V-Flash 模型分析图片、视频或文件，返回文字描述。可同时分析多个资源（用逗号分隔），支持网络 URL 和本地文件路径。

- **输入**：
  - `urls`：**string**，必填。单个 URL 或本地路径，多个请用英文逗号分隔（例如 `"a.jpg,b.png"`）。本地文件会自动转为 base64 编码的 data URL 发送。
  - `prompt`：**string**，必填。要问的问题，如“这张图片里有什么？”或“总结这段视频内容”。
  - `type`：**string**，可选，默认为 `"image_url"`。可选值 `"image_url"`（图片）、`"video_url"`（视频）、`"file_url"`（文档等）。根据资源类型选择。

- **输出**：成功时返回文字描述，失败时返回错误信息。

- **配置**：本工具依赖智谱 API。在项目根目录的 `config.json` 中，可以单独为 `ett` 工具配置 API 参数（位于 `tools.ett` 下），若不配置则自动使用顶层的 `api_key`、`base_url` 等。例如：

```json
{
  "api_key": "your-chat-api-key",
  "base_url": "https://open.bigmodel.cn/api/paas/v4",
  "model": "glm-4.7-flash",
  "tools": {
    "ett": {
      "api_key": "your-ett-api-key",
      "base_url": "https://open.bigmodel.cn/api/paas/v4",
      "model": "glm-4.6v-flash",
      "temperature": 0.8,
      "thinking": false
    }
  }
}
```