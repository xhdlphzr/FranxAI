# Copyright (C) 2026 xhdlphzr
# This file is part of FranxAgent.
# FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
# FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

"""
File Content Reading Tool
Allows the AI to read the content of a specified file or project structure
"""

from pathlib import Path
import json
import base64
import time
from openai import OpenAI
from markitdown import MarkItDown

# tree-sitter core
from tree_sitter import Language, Parser

# Language grammars
import tree_sitter_c as tsc
import tree_sitter_cpp as tscpp
import tree_sitter_python as tspython
import tree_sitter_java as tsjava
import tree_sitter_rust as tsrust
import tree_sitter_go as tsgo
import tree_sitter_javascript as tsjs
import tree_sitter_html as tshtml
import tree_sitter_css as tscss
import tree_sitter_typescript as tstypescript
import tree_sitter_c_sharp as tscs

# Language registry: suffix -> (Language, target_node_types)
LANGUAGES = {
    '.py': (Language(tspython.language()), ['function_definition', 'class_definition', 'import_statement', 'import_from_statement']),
    '.pyw': (Language(tspython.language()), ['function_definition', 'class_definition', 'import_statement', 'import_from_statement']),
    '.js': (Language(tsjs.language()), ['function_declaration', 'class_declaration', 'import_statement', 'export_statement', 'lexical_declaration', 'variable_declaration']),
    '.jsx': (Language(tsjs.language()), ['function_declaration', 'class_declaration', 'import_statement', 'export_statement']),
    '.ts': (Language(tstypescript.language_typescript()), ['function_declaration', 'class_declaration', 'interface_declaration', 'type_alias_declaration', 'import_statement', 'export_statement', 'abstract_class_declaration', 'lexical_declaration']),
    '.tsx': (Language(tstypescript.language_tsx()), ['function_declaration', 'class_declaration', 'interface_declaration', 'type_alias_declaration', 'import_statement', 'export_statement']),
    '.rs': (Language(tsrust.language()), ['function_item', 'impl_item', 'struct_item', 'enum_item', 'trait_item', 'use_declaration', 'mod_item']),
    '.go': (Language(tsgo.language()), ['function_declaration', 'method_declaration', 'type_declaration', 'import_declaration']),
    '.java': (Language(tsjava.language()), ['class_declaration', 'method_declaration', 'interface_declaration', 'import_declaration', 'constructor_declaration']),
    '.c': (Language(tsc.language()), ['function_definition', 'struct_specifier', 'enum_specifier', 'preproc_include', 'type_definition']),
    '.h': (Language(tsc.language()), ['function_definition', 'struct_specifier', 'enum_specifier', 'preproc_include', 'type_definition']),
    '.cpp': (Language(tscpp.language()), ['function_definition', 'class_specifier', 'struct_specifier', 'namespace_definition', 'preproc_include', 'template_declaration']),
    '.hpp': (Language(tscpp.language()), ['function_definition', 'class_specifier', 'struct_specifier', 'namespace_definition', 'preproc_include', 'template_declaration']),
    '.cc': (Language(tscpp.language()), ['function_definition', 'class_specifier', 'struct_specifier', 'namespace_definition', 'preproc_include', 'template_declaration']),
    '.cs': (Language(tscs.language()), ['class_declaration', 'method_declaration', 'interface_declaration', 'namespace_declaration', 'using_directive', 'struct_declaration', 'enum_declaration']),
    '.html': (Language(tshtml.language()), ['element']),
    '.htm': (Language(tshtml.language()), ['element']),
    '.css': (Language(tscss.language()), ['rule_set']),
}

# Directories to skip during project scanning
SKIP_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build', 'target', '.idea', '.vscode', 'env', '.env', '.tox', '.mypy_cache', '.pytest_cache', 'egg-info'}

def _extract_name(node) -> str:
    """Extract the name of an AST node using tree-sitter fields"""
    # Prefer 'name' field (works for most languages' class, function, method, etc.)
    name_node = node.child_by_field_name('name')
    if name_node:
        return name_node.text.decode('utf-8')
    
    # Fallback: for import, export, namespace etc. that lack a name field
    for child in node.children:
        if child.type in ('identifier', 'type_identifier', 'field_identifier'):
            return child.text.decode('utf-8')
    return ""

def _parse_structure(path: Path, content: str) -> str | None:
    """Parse code file structure, return skeleton summary"""
    suffix = path.suffix.lower()
    if suffix not in LANGUAGES:
        return None

    lang, target_types = LANGUAGES[suffix]
    parser = Parser(lang)

    tree = parser.parse(content.encode('utf-8'))
    
    lines = []
    def walk(node, depth=0):
        if node.type in target_types:
            start = node.start_point.row + 1
            end = node.end_point.row + 1
            name = _extract_name(node)
            display_name = f" {name}" if name else ""
            prefix = "  " * depth + ("├─ " if depth > 0 else "")
            lines.append(f"{prefix}[{node.type}]{display_name} (L{start}-L{end})")
            # Target node found, continue into its children with depth + 1
            for child in node.children:
                walk(child, depth + 1)
        else:
            # Non-target node, continue walking children without increasing depth
            for child in node.children:
                walk(child, depth)

    walk(tree.root_node)
    return "\n".join(lines) if lines else None

def _add_line_numbers(content: str) -> str:
    """Add line numbers to text"""
    lines = content.split('\n')
    width = len(str(len(lines)))
    return '\n'.join(f"{i+1:{width}}  {line}" for i, line in enumerate(lines))

def _scan_project(directory: Path) -> str:
    """Scan project directory, return structure map of all code files"""
    lines = []
    
    for file in sorted(directory.rglob('*')):
        # Skip hidden and common junk directories
        if any(part in SKIP_DIRS or part.startswith('.') for part in file.parts):
            continue
        if not file.is_file():
            continue
        if file.suffix.lower() not in LANGUAGES:
            continue
        
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
            structure = _parse_structure(file, content)
            if structure:
                rel = file.relative_to(directory)
                lines.append(f"### {rel}")
                lines.append(structure)
                lines.append("")
        except Exception:
            continue
    
    return "\n".join(lines) if lines else "No parseable code files found"

def read(path: str) -> str:
    """
    Read file content or project structure

    Args:
        path: Full path of the file or directory

    Returns:
        File content or project structure, returns error message if an error occurs
    """
    try:
        # Resolve the path and handle user directory symbol (~)
        p = Path(path).expanduser().resolve()

        # Check if the path exists
        if not p.exists():
            return f"Error: Path does not exist - {p}"

        # Directory: scan project structure
        if p.is_dir():
            return _scan_project(p)

        # File: read content
        with open(p, 'r', encoding='utf-8') as f:
            content = f.read()

        # Three-tier fallback: parsed + numbered -> numbered only -> raw text
        try:
            structure = _parse_structure(p, content)
            numbered = _add_line_numbers(content)
            if structure:
                return f"structure\n{structure}\n\ncontent\n{numbered}"
            else:
                return numbered
        except Exception:
            return content

    except PermissionError:
        return f"Error: No permission to read - {path}"
    except Exception as e:
        return f"An error occurred while reading: {str(e)}"
    
def _get_config():
    """Read ett tool configuration from config.json"""
    config_path = Path(__file__).parent.parent.parent / "config.json"
    if not config_path.exists():
        raise FileNotFoundError("config.json not found")
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
    """Convert local file to data URL"""
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    ext = Path(path).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".gif": "image/gif", ".mp4": "video/mp4", ".webm": "video/webm"
    }
    mime = mime_map.get(ext, "application/octet-stream")
    return f"data:{mime};base64,{data}"

def ett(urls: str) -> str:
    cfg = _get_config()
    prompt = "Please describe the following content in detail"
    if urls.endswith(('.jpg', '.png', '.gif', '.jpeg')):
        ftype = "image_url"
    if urls.endswith(('.mp4', '.webm')):
        ftype = "video_url"
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])

    # Parse URLs
    url_list = [u.strip() for u in urls.split(",") if u.strip()]
    processed_urls = []
    for url in url_list:
        if url.startswith(("http://", "https://")):
            processed_urls.append(url)
        else:
            try:
                print("Encoding local file to base64, large files may take time please wait...")
                data_url = _encode_local_file(url)
                processed_urls.append(data_url)
            except Exception as e:
                return f"Failed to process local file: {e}"

    # Build content structure
    content = []
    for u in processed_urls:
        if ftype == "image_url":
            content.append({"type": "image_url", "image_url": {"url": u}})
        elif ftype == "video_url":
            content.append({"type": "video_url", "video_url": {"url": u}})
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
                timeout=60.0,   # Request timeout
                extra_body={"thinking": {"type": "disabled"}} if not cfg["thinking"] else None
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            # Judge temporary errors: 429, 500, timeout or rate limit keywords
            if any(code in error_msg for code in ["429", "500", "timed out", "timeout"]) or "rate" in error_msg.lower() or "too many" in error_msg.lower():
                if attempt < max_retries - 1:
                    wait = base_delay * (2 ** attempt)
                    print(f"Temporary API error, retry after {wait} seconds...")
                    time.sleep(wait)
                    continue
                else:
                    return "Analysis failed: API busy or timeout, please try again later. Copy content as text or screenshot to retry."
            else:
                return f"Analysis failed: {e}"

    return "Analysis failed: Maximum retries exceeded, please try again later."

def execute(path: str) -> str:
    # Directory: scan project structure
    if Path(path).expanduser().is_dir():
        return read(path)
    if path.endswith(('.pdf', '.docx', '.pptx', '.xlsx', '.xls', '.doc', '.ppt', '.csv')):
        try:
            return MarkItDown().convert(path).text_content
        except Exception as e:
            return f"Failed to convert file to Markdown: {e}"
    elif path.endswith(('.jpg', '.png', '.gif', '.mp4', '.webm', '.jpeg')):
        return ett(path)
    else:
        return read(path)