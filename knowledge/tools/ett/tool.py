# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

import json
import base64
import time
from pathlib import Path
from openai import OpenAI

def _get_config():
    """Read ett tool configuration from config.json | 从 config.json 读取 ett 工具配置"""
    config_path = Path(__file__).parent.parent.parent / "config.json"
    if not config_path.exists():
        raise FileNotFoundError("config.json not found | 未找到 config.json")
    with open(config_path, 'r', encoding='utf-8') as f:
        full_config = json.load(f)
    tool_cfg = full_config.get("tools", {}).get("ett", {})
    return {
        "api_key": tool_cfg.get("api_key", full_config.get("api_key")),
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": tool_cfg.get("model", "glm-4.6v-flash"),
        "temperature": tool_cfg.get("temperature", full_config.get("temperature", 0.8)),
        "thinking": tool_cfg.get("thinking", full_config.get("thinking", False)),
        "max_retries": tool_cfg.get("max_retries", 5),
    }

def _encode_local_file(path: str) -> str:
    """Convert local file to data URL | 将本地文件转为 data URL"""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    ext = Path(path).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".mp4": "video/mp4", ".webm": "video/webm",
        ".pdf": "application/pdf", ".txt": "text/plain",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword"
    }
    mime = mime_map.get(ext, "application/octet-stream")
    return f"data:{mime};base64,{data}"

def execute(urls: str, prompt: str, type: str = "image_url") -> str:
    cfg = _get_config()
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])

    # Parse URLs | 解析 URLs
    url_list = [u.strip() for u in urls.split(",") if u.strip()]
    processed_urls = []
    for url in url_list:
        if url.startswith(("http://", "https://")):
            processed_urls.append(url)
        else:
            try:
                print("Encoding local file to base64, large files may take time please wait... | 本地文件base64转码中，如果是大文件，可能需要较长时间，请稍后...")
                data_url = _encode_local_file(url)
                processed_urls.append(data_url)
            except Exception as e:
                return f"Failed to process local file: {e} | 处理本地文件失败: {e}"

    # Build content structure | 构建 content
    content = []
    for u in processed_urls:
        if type == "image_url":
            content.append({"type": "image_url", "image_url": {"url": u}})
        elif type == "video_url":
            content.append({"type": "video_url", "video_url": {"url": u}})
        elif type == "file_url":
            content.append({"type": "file_url", "file_url": {"url": u}})
        else:
            return f"Unsupported type: {type} | 不支持的 type: {type}"
    content.append({"type": "text", "text": prompt})
    messages = [{"role": "user", "content": content}]

    max_retries = cfg["max_retries"]
    base_delay = 2

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=cfg["model"],
                messages=messages,
                temperature=cfg["temperature"],
                stream=False,
                timeout=60.0,   # Request timeout | 超时
                extra_body={"thinking": {"type": "disabled"}} if not cfg["thinking"] else None
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            # Judge temporary errors: 429、500、timeout or rate limit keywords | 判断临时错误：429、500、timeout 或 rate/too many 关键词
            if any(code in error_msg for code in ["429", "500", "timed out", "timeout"]) or "rate" in error_msg.lower() or "too many" in error_msg.lower():
                if attempt < max_retries - 1:
                    wait = base_delay * (2 ** attempt)
                    print(f"Temporary API error, retry after {wait} seconds... | API 临时错误，等待 {wait} 秒后重试...")
                    time.sleep(wait)
                    continue
                else:
                    return "Analysis failed: API busy or timeout, please try again later. Copy content as text or screenshot to retry. | 分析失败: 当前 API 服务繁忙或超时，请稍后再试。建议将文件内容复制为文本或截图后重新发送。"
            else:
                return f"Analysis failed: {e} | 分析失败: {e}"

    return "Analysis failed: Maximum retries exceeded, please try again later. | 分析失败: 超过重试次数，请稍后再试。"