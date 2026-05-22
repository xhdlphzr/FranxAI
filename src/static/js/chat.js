// Copyright (C) 2026 xhdlphzr
// This file is part of FranxAgent.
// FranxAgent is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
// FranxAgent is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
// You should have received a copy of the GNU Affero General Public License along with FranxAgent.  If not, see <https://www.gnu.org/licenses/>.

window.katexDisableDollar = true;
const chatMessages = document.getElementById("chat-messages");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");
window.chatMessages = chatMessages;

let currentAbortController = null;
let isGenerating = false;
let currentUserMessage = "";
let currentPartialText = "";
let currentAssistantMsgDiv = null;
let currentKnowledgeItems = [];
let currentKnowledgeBlock = null;

/**
 * Check whether the user is currently scrolled near the bottom of the chat.
 * @returns {boolean}
 */
function isUserAtBottom() {
  const el = window.chatMessages;
  if (!el) return false;
  // Allow a small buffer (10px) so that slight variations don't break the detection
  return el.scrollTop + el.clientHeight >= el.scrollHeight - 10;
}

/**
 * Scroll the chat container to the very bottom immediately.
 */
function scrollToBottom() {
  const el = window.chatMessages;
  if (!el) return;
  el.scrollTo({
    top: el.scrollHeight,
    behavior: "smooth",
  });
}

/**
 * Highlight all unprocessed code blocks inside a container using highlight.js.
 * @param {HTMLElement} container
 */
function highlightCodeBlocks(container) {
  if (!container) return;
  // Select all code blocks that haven't been highlighted yet (no 'hljs' class).
  container.querySelectorAll("pre code:not(.hljs)").forEach((block) => {
    hljs.highlightElement(block);
  });
}

/**
 * Render all unprocessed Mermaid code blocks inside a container as SVG diagrams.
 * @param {HTMLElement} container
 */
async function renderMermaidBlocks(container) {
  if (!container) return;
  const blocks = container.querySelectorAll(
    "pre code.language-mermaid:not(.mermaid-rendered)",
  );
  for (const code of blocks) {
    const pre = code.parentElement;
    const mermaidCode = code.textContent;
    try {
      const id = "mermaid-" + Math.random().toString(36).substr(2, 9);
      const { svg } = await mermaid.render(id, mermaidCode);
      const wrapper = document.createElement("div");
      wrapper.className = "mermaid-wrapper";
      wrapper.innerHTML = svg;
      pre.replaceWith(wrapper);
    } catch (err) {
      console.error("Mermaid render failed:", err);
      pre.innerHTML = `<div class="mermaid-error">Mermaid render error: ${err.message}</div>`;
    }
  }
}

function escapeHtml(str) {
  return str.replace(/[&<>]/g, function (m) {
    if (m === "&") return "&amp;";
    if (m === "<") return "&lt;";
    if (m === ">") return "&gt;";
    return m;
  });
}

function sanitizeForMarkdown(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function wrapTables(container) {
  container.querySelectorAll("table").forEach((table) => {
    if (table.parentElement.classList.contains("table-scroll-wrapper")) return;
    const wrapper = document.createElement("div");
    wrapper.className = "table-scroll-wrapper";
    table.parentNode.insertBefore(wrapper, table);
    wrapper.appendChild(table);
  });
}

function renderStreamingMarkdown(msgDiv, rawText) {
  msgDiv._rawText = rawText;
  let contentContainer = msgDiv.querySelector(
    ".assistant-content:last-of-type",
  );
  if (!contentContainer) {
    contentContainer = document.createElement("div");
    contentContainer.className = "assistant-content";
    msgDiv.appendChild(contentContainer);
  }
  try {
    const html = marked.parse(rawText);
    contentContainer.innerHTML = html;
  } catch (e) {
    contentContainer.textContent = rawText;
  }
  wrapTables(contentContainer);
  // Apply code highlighting to the freshly rendered Markdown
  highlightCodeBlocks(contentContainer);
  renderMermaidBlocks(contentContainer);
  const existingDot = contentContainer.querySelector(".typing-dot");
  if (existingDot) existingDot.remove();
  const dot = document.createElement("span");
  dot.className = "typing-dot";
  const lastChild = contentContainer.lastElementChild;
  if (lastChild) {
    lastChild.appendChild(dot);
  } else {
    contentContainer.appendChild(dot);
  }
}

function updateKnowledgeBlock(msgDiv, knowledgeItems) {
  msgDiv._knowledgeItems = knowledgeItems;
  if (!knowledgeItems.length) {
    if (currentKnowledgeBlock) currentKnowledgeBlock.remove();
    currentKnowledgeBlock = null;
    return;
  }
  // If currentKnowledgeBlock belongs to a different message, reset it
  if (currentKnowledgeBlock && currentKnowledgeBlock.parentElement !== msgDiv) {
    currentKnowledgeBlock = null;
  }
  if (!currentKnowledgeBlock) {
    currentKnowledgeBlock = document.createElement("div");
    currentKnowledgeBlock.className = "assistant-block knowledge-block";
    const header = document.createElement("div");
    header.className = "block-header";
    const icon = document.createElement("span");
    icon.className = "toggle-icon";
    icon.textContent = "▶";
    header.appendChild(icon);
    header.appendChild(
      document.createTextNode(
        t("knowledge.title") + " (" + knowledgeItems.length + ")",
      ),
    );
    const contentDiv = document.createElement("div");
    contentDiv.className = "block-content";
    const inner = document.createElement("div");
    inner.style.display = "flex";
    inner.style.flexDirection = "column";
    inner.style.gap = "0.75rem";
    contentDiv.appendChild(inner);
    currentKnowledgeBlock.appendChild(header);
    currentKnowledgeBlock.appendChild(contentDiv);
    header.addEventListener("click", () => {
      const isOpen = contentDiv.classList.contains("show");
      if (isOpen) {
        contentDiv.classList.remove("show");
        icon.textContent = "▶";
      } else {
        contentDiv.classList.add("show");
        icon.textContent = "▼";
      }
    });
    msgDiv.insertBefore(currentKnowledgeBlock, msgDiv.firstChild);
  }
  const inner = currentKnowledgeBlock.querySelector(".block-content > div");
  inner.innerHTML = "";
  knowledgeItems.forEach((text) => {
    let summary = "";
    const titleMatch = text.match(/^###\s+(.+)$/m);
    if (titleMatch) summary = titleMatch[1];
    else summary = text.substring(0, 50) + (text.length > 50 ? "…" : "");
    const itemDiv = document.createElement("div");
    itemDiv.className = "knowledge-item";
    const sumDiv = document.createElement("div");
    sumDiv.className = "knowledge-summary";
    sumDiv.innerHTML = `📄 ${escapeHtml(summary)} <span style="font-size:0.7rem;">▼</span>`;
    const fullDiv = document.createElement("div");
    fullDiv.className = "knowledge-full";
    try {
      const html = marked.parse(text);
      fullDiv.innerHTML = html;
      wrapTables(fullDiv);
      // Highlight code blocks inside knowledge items
      highlightCodeBlocks(fullDiv);
      renderMermaidBlocks(fullDiv);
      if (window.renderMathInElement) {
        window.renderMathInElement(fullDiv, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false },
          ],
        });
      }
    } catch (e) {
      fullDiv.textContent = text;
    }
    sumDiv.addEventListener("click", (e) => {
      e.stopPropagation();
      fullDiv.classList.toggle("show");
      const iconSpan = sumDiv.querySelector("span");
      if (fullDiv.classList.contains("show")) {
        iconSpan.textContent = "▼";
      } else {
        iconSpan.textContent = "▶";
      }
    });
    itemDiv.appendChild(sumDiv);
    itemDiv.appendChild(fullDiv);
    inner.appendChild(itemDiv);
  });
  const header = currentKnowledgeBlock.querySelector(".block-header");
  header.lastChild.textContent =
    t("knowledge.title") + " (" + knowledgeItems.length + ")";
}

function addToolCallBlockStructured(
  msgDiv,
  callId,
  toolName,
  argumentsObj,
  resultText,
) {
  let params = argumentsObj;
  if (params && typeof params === "object") {
    if (
      "arguments" in params &&
      params.arguments &&
      typeof params.arguments === "object"
    ) {
      params = params.arguments;
    }
  }
  if (!params || typeof params !== "object") params = {};
  if (typeof toolName !== "string") {
    toolName = String(toolName);
  }
  const blockDiv = document.createElement("div");
  blockDiv.className = "assistant-block tool-call-block";
  blockDiv.dataset.callId = callId;
  const header = document.createElement("div");
  header.className = "block-header";
  header.dataset.toolName = toolName;
  const icon = document.createElement("span");
  icon.className = "toggle-icon";
  icon.textContent = "▶";
  header.appendChild(icon);
  header.appendChild(
    document.createTextNode(t("tool.using", { name: toolName })),
  );
  const paramsDiv = document.createElement("div");
  paramsDiv.className = "tool-params";
  if (Object.keys(params).length > 0) {
    for (const [key, value] of Object.entries(params)) {
      const paramLine = document.createElement("div");
      paramLine.className = "tool-param";
      let valStr =
        typeof value === "object"
          ? JSON.stringify(value, null, 2)
          : String(value);
      paramLine.textContent = `${key}: ${valStr}`;
      paramsDiv.appendChild(paramLine);
    }
  } else {
    const fallback = document.createElement("div");
    fallback.className = "tool-param";
    fallback.textContent = t("tool.no_params");
    paramsDiv.appendChild(fallback);
  }
  const resultLabel = document.createElement("div");
  resultLabel.className = "tool-param";
  resultLabel.style.fontWeight = "bold";
  resultLabel.style.marginTop = "0.5rem";
  resultLabel.textContent = t("tool.result");
  paramsDiv.appendChild(resultLabel);
  const resultContent = document.createElement("div");
  resultContent.className = "tool-param";
  resultContent.style.padding = "0.25rem 0";
  if (resultText && resultText !== "null" && resultText !== "") {
    resultContent.textContent = resultText;
    header.lastChild.textContent = t("tool.used", { name: toolName });
  } else {
    resultContent.textContent = t("tool.executing");
    resultContent.classList.add("tool-result-pending");
  }
  paramsDiv.appendChild(resultContent);
  blockDiv.appendChild(header);
  blockDiv.appendChild(paramsDiv);
  header.addEventListener("click", () => {
    const isOpen = paramsDiv.classList.contains("show");
    if (isOpen) {
      paramsDiv.classList.remove("show");
      icon.textContent = "▶";
    } else {
      paramsDiv.classList.add("show");
      icon.textContent = "▼";
    }
  });
  msgDiv.appendChild(blockDiv);
  return blockDiv;
}

function updateToolCallResult(msgDiv, callId, resultText) {
  const blockDiv = msgDiv.querySelector(
    `.tool-call-block[data-call-id="${callId}"]`,
  );
  if (!blockDiv) return;
  const header = blockDiv.querySelector(".block-header");
  if (header) {
    const toolName = header.dataset.toolName;
    header.lastChild.textContent = t("tool.used", { name: toolName });
  }
  const pendingResult = blockDiv.querySelector(".tool-result-pending");
  if (pendingResult) {
    pendingResult.textContent = resultText;
    pendingResult.classList.remove("tool-result-pending");
  } else {
    const resultContent = blockDiv.querySelectorAll(".tool-param")[1];
    if (resultContent) resultContent.textContent = resultText;
  }
}

function addConfirmationBlock(msgDiv, confirmId, toolName, argumentsObj) {
  let params = argumentsObj;
  if (params && typeof params === "object") {
    if (
      "arguments" in params &&
      params.arguments &&
      typeof params.arguments === "object"
    ) {
      params = params.arguments;
    }
    if ("tool_name" in params && "arguments" in params) {
      params = params.arguments;
    }
  }
  if (!params || typeof params !== "object") params = {};
  const blockDiv = document.createElement("div");
  blockDiv.className = "confirm-block";
  blockDiv.dataset.confirmId = confirmId;
  const header = document.createElement("div");
  header.className = "confirm-header";
  header.textContent = t("tool.confirm", { name: toolName });
  blockDiv.appendChild(header);
  const paramsDiv = document.createElement("div");
  paramsDiv.className = "confirm-params";
  let displayParams = "";
  if (toolName === "write") {
    const path = params.path || "";
    const mode = params.mode || "overwrite";
    const content = params.content || "";
    const startLine = params.start_line || 0;
    const endLine = params.end_line || 0;
    displayParams = t("tool.confirm_write_template", {
      path,
      mode,
      content,
      startLine,
      endLine,
    });
  } else if (toolName === "command") {
    const command = params.command || "";
    displayParams = t("tool.confirm_command_template", { command });
  } else {
    displayParams = JSON.stringify(params, null, 2);
  }
  try {
    paramsDiv.innerHTML = marked.parse(displayParams);
  } catch (e) {
    paramsDiv.textContent = displayParams;
  }
  blockDiv.appendChild(paramsDiv);
  const buttonsDiv = document.createElement("div");
  buttonsDiv.className = "confirm-buttons";
  const approveBtn = document.createElement("button");
  approveBtn.className = "confirm-approve";
  approveBtn.textContent = t("tool.approve");
  const rejectBtn = document.createElement("button");
  rejectBtn.className = "confirm-reject";
  rejectBtn.textContent = t("tool.reject");
  buttonsDiv.appendChild(approveBtn);
  buttonsDiv.appendChild(rejectBtn);
  blockDiv.appendChild(buttonsDiv);
  approveBtn.addEventListener("click", async () => {
    try {
      await fetchWithAuth("/api/confirm_tool", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirm_id: confirmId, approved: true }),
      });
      blockDiv.remove();
    } catch (err) {
      console.error("Failed to send approval", err);
    }
  });
  rejectBtn.addEventListener("click", async () => {
    try {
      await fetchWithAuth("/api/confirm_tool", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirm_id: confirmId, approved: false }),
      });
      blockDiv.innerHTML = `<div class="confirm-header">${t("tool.rejected")}</div>`;
    } catch (err) {
      console.error("Failed to send rejection", err);
    }
  });
  msgDiv.appendChild(blockDiv);
  return blockDiv;
}

function saveMessagesToLocalStorage() {
  const messages = [];
  document.querySelectorAll(".message").forEach((msgDiv) => {
    const role = msgDiv.classList.contains("user") ? "user" : "assistant";
    if (!msgDiv.classList.contains("temp")) {
      const msg = { role };
      if (role === "assistant") {
        if (msgDiv._rawText) {
          msg.content = msgDiv._rawText;
        } else if (msgDiv._textNode) {
          msg.content = msgDiv._textNode.textContent;
        } else {
          msg.content = msgDiv.textContent;
        }
        if (msgDiv._knowledgeItems && msgDiv._knowledgeItems.length > 0) {
          msg.knowledge = msgDiv._knowledgeItems;
        }
      } else {
        msg.content = msgDiv.textContent;
      }
      messages.push(msg);
    }
  });
  localStorage.setItem("chatMessages", JSON.stringify(messages));
}

function loadMessagesFromLocalStorage() {
  const stored = localStorage.getItem("chatMessages");
  if (stored) {
    const messages = JSON.parse(stored);
    messages.forEach((msg) => {
      const msgDiv = addMessage(msg.role, msg.content, false, "", true);
      if (
        msg.role === "assistant" &&
        msg.knowledge &&
        msg.knowledge.length > 0
      ) {
        msgDiv._knowledgeItems = msg.knowledge;
        updateKnowledgeBlock(msgDiv, msg.knowledge);
      }
    });
    window.chatMessages.scrollTop = window.chatMessages.scrollHeight;
  }
}

function addMessage(
  role,
  content,
  temporary = false,
  extraClass = "",
  parseMarkdown = false,
) {
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${role} ${extraClass}`;
  if (temporary) msgDiv.classList.add("temp");
  if (role === "assistant" && temporary) {
    msgDiv._rawText = "";
    const contentContainer = document.createElement("div");
    contentContainer.className = "assistant-content";
    msgDiv.appendChild(contentContainer);
    renderStreamingMarkdown(msgDiv, content);
  } else if (parseMarkdown && !temporary) {
    if (role === "user") {
      const safeContent = sanitizeForMarkdown(content);
      const html = marked.parse(safeContent);
      msgDiv.innerHTML = html;
    } else {
      const html = marked.parse(content);
      msgDiv.innerHTML = html;
    }
    wrapTables(msgDiv);
    // Highlight code blocks in the fully rendered message
    highlightCodeBlocks(msgDiv);
    renderMermaidBlocks(msgDiv);
    if (window.renderMathInElement) {
      window.renderMathInElement(msgDiv, {
        delimiters: [
          { left: "$$", right: "$$", display: true },
          { left: "$", right: "$", display: false },
        ],
      });
    }
  } else {
    msgDiv.textContent = content;
  }
  chatMessages.appendChild(msgDiv);
  if (!temporary) saveMessagesToLocalStorage();
  return msgDiv;
}

function updateMessage(msgDiv, content) {
  msgDiv._rawText = content;
  const contentContainer = msgDiv.querySelector(".assistant-content");
  if (contentContainer) {
    try {
      const html = marked.parse(content);
      contentContainer.innerHTML = html;
      wrapTables(contentContainer);
      // Highlight freshly rendered code
      highlightCodeBlocks(contentContainer);
      renderMermaidBlocks(contentContainer);
      let dot = contentContainer.querySelector(".typing-dot");
      if (!dot) {
        dot = document.createElement("span");
        dot.className = "typing-dot";
      } else {
        dot.remove();
      }
      const lastChild = contentContainer.lastElementChild;
      if (lastChild) lastChild.appendChild(dot);
      else contentContainer.appendChild(dot);
    } catch (e) {
      contentContainer.textContent = content;
    }
  } else {
    msgDiv.textContent = content;
  }
  msgDiv.classList.remove("temp");
  saveMessagesToLocalStorage();
}

function removeTypingDot(msgDiv) {
  const lastContainer = msgDiv.querySelector(".assistant-content:last-of-type");
  if (lastContainer) {
    const dot = lastContainer.querySelector(".typing-dot");
    if (dot) dot.remove();
  }
}

function setSendButtonToStop() {
  sendBtn.textContent = t("chat.stop");
  sendBtn.removeEventListener("click", sendMessage);
  sendBtn.addEventListener("click", stopGeneration);
}

function setSendButtonToSend() {
  sendBtn.textContent = t("chat.send");
  sendBtn.removeEventListener("click", stopGeneration);
  sendBtn.addEventListener("click", sendMessage);
}

function stopGeneration() {
  if (currentAbortController) {
    currentAbortController.abort();
    currentAbortController = null;
  }
  setSendButtonToSend();
  isGenerating = false;
  if (currentPartialText && currentUserMessage) {
    fetchWithAuth("/api/save_partial", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_message: currentUserMessage,
        partial_response: currentPartialText,
      }),
    }).catch((e) => console.error("Failed to save partial response", e));
    if (currentAssistantMsgDiv) {
      const stopText = currentPartialText + "\n\n" + t("chat.stopped");
      currentAssistantMsgDiv._rawText = stopText;
      const contentContainer =
        currentAssistantMsgDiv.querySelector(".assistant-content");
      if (contentContainer) {
        try {
          contentContainer.innerHTML = marked.parse(stopText);
          wrapTables(contentContainer);
          // Highlight code blocks when user stops generation
          highlightCodeBlocks(contentContainer);
          renderMermaidBlocks(contentContainer);
        } catch (e) {
          contentContainer.textContent = stopText;
        }
      }
      removeTypingDot(currentAssistantMsgDiv);
      currentAssistantMsgDiv.classList.remove("temp");
      saveMessagesToLocalStorage();
    } else {
      addMessage("assistant", currentPartialText + "\n\n" + t("chat.stopped"));
    }
  } else {
    addMessage("assistant", t("chat.stopped"));
  }
  currentUserMessage = "";
  currentPartialText = "";
  currentAssistantMsgDiv = null;
  currentKnowledgeItems = [];
  currentKnowledgeBlock = null;
}

async function sendMessage() {
  currentKnowledgeItems = [];
  if (currentKnowledgeBlock) {
    currentKnowledgeBlock.remove();
    currentKnowledgeBlock = null;
  }
  const message = messageInput.value.trim();
  if (!message || isGenerating) return;
  isGenerating = true;
  messageInput.value = "";
  currentUserMessage = message;
  currentPartialText = "";
  currentAbortController = new AbortController();
  const signal = currentAbortController.signal;
  setSendButtonToStop();
  addMessage("user", message, false, "", true);
  scrollToBottom();
  const assistantMsgDiv = addMessage(
    "assistant",
    t("chat.thinking"),
    true,
    "",
    false,
  );
  currentAssistantMsgDiv = assistantMsgDiv;
  let fullText = "";
  let receivedHtml = false;
  try {
    const resp = await fetchWithAuth("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
      signal,
    });
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const data = JSON.parse(line.substring(6));
            if (data.type === "content") {
              fullText += data.text;
              currentPartialText = fullText;
              renderStreamingMarkdown(assistantMsgDiv, fullText);
              assistantMsgDiv.classList.remove("temp");
              // Smart scroll: only auto-scroll when the user is at the bottom
              if (isUserAtBottom()) {
                scrollToBottom();
              }
            } else if (data.type === "tool_call") {
              removeTypingDot(assistantMsgDiv);
              assistantMsgDiv.classList.remove("temp");
              addToolCallBlockStructured(
                assistantMsgDiv,
                data.call_id,
                data.tool_name,
                data.arguments,
                data.result,
              );
              const newContainer = document.createElement("div");
              newContainer.className = "assistant-content";
              assistantMsgDiv.appendChild(newContainer);
              fullText = "";
            } else if (data.type === "tool_result") {
              updateToolCallResult(assistantMsgDiv, data.call_id, data.result);
            } else if (data.type === "html") {
              receivedHtml = true;
              removeTypingDot(assistantMsgDiv);
              assistantMsgDiv.classList.remove("temp");
              if (window.renderMathInElement) {
                window.renderMathInElement(assistantMsgDiv, {
                  delimiters: [
                    { left: "$$", right: "$$", display: true },
                    { left: "$", right: "$", display: false },
                  ],
                });
              }
              saveMessagesToLocalStorage();
            } else if (data.type === "knowledge") {
              currentKnowledgeItems.push(data.text);
              updateKnowledgeBlock(assistantMsgDiv, currentKnowledgeItems);
            } else if (data.type === "confirmation_required") {
              addConfirmationBlock(
                assistantMsgDiv,
                data.confirm_id,
                data.tool_name,
                data.arguments,
              );
            } else if (data.type === "write_proposal") {
              await handleWriteProposal(assistantMsgDiv, data);
            } else if (data.type === "error") {
              updateMessage(
                assistantMsgDiv,
                t("chat.error", { message: data.text }),
              );
              removeTypingDot(assistantMsgDiv);
            }
          } catch (e) {
            console.error(e);
          }
        }
      }
    }
    if (assistantMsgDiv.querySelector(".typing-dot")) {
      removeTypingDot(assistantMsgDiv);
      saveMessagesToLocalStorage();
    }
  } catch (err) {
    if (err.name !== "AbortError") {
      updateMessage(
        assistantMsgDiv,
        t("chat.network_error", { message: err.message }),
      );
      removeTypingDot(assistantMsgDiv);
    }
  } finally {
    setSendButtonToSend();
    isGenerating = false;
    currentAbortController = null;
    currentUserMessage = "";
    currentPartialText = "";
    currentAssistantMsgDiv = null;
    currentKnowledgeItems = [];
    currentKnowledgeBlock = null;
  }
}

messageInput.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key === "Enter") sendMessage();
});

// Automatic code highlighting
(function () {
  const chat = document.getElementById("chat-messages");
  if (!chat) return;

  // Watch for new nodes added to the chat area
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        // Only process element nodes
        if (node.nodeType === Node.ELEMENT_NODE) {
          node.querySelectorAll("pre code:not(.hljs)").forEach((block) => {
            // Ensure a language class exists, otherwise treat as plain text
            if (!block.className.includes("language-")) {
              block.classList.add("language-text");
            }
            hljs.highlightElement(block);
          });
        }
      });
    });
  });

  observer.observe(chat, { childList: true, subtree: true });

  // Also highlight any code blocks already present on page load
  chat.querySelectorAll("pre code:not(.hljs)").forEach((block) => {
    if (!block.className.includes("language-")) {
      block.classList.add("language-text");
    }
    hljs.highlightElement(block);
  });
})();

/**
 * Handle a write_proposal SSE event: fetch the original file, create the
 * code review panel in split-layout mode, and wire up approve/reject.
 * @param {HTMLElement} msgDiv - The assistant message element
 * @param {Object} data - The write_proposal event data
 */
async function handleWriteProposal(msgDiv, data) {
  const confirmId = data.confirm_id;
  const aiContent = data.content || "";

  let args = data.arguments || {};
  if (args.arguments && typeof args.arguments === "object") {
    args = args.arguments;
  }

  const path = args.path || "";
  console.log("Write proposal for path:", path);

  // Fetch original file content
  let originalText = "";
  try {
    const resp = await fetchWithAuth("/api/read_file", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    });
    const result = await resp.json();
    originalText = result.content || "";
  } catch (e) {
    console.error("Failed to read original file:", e);
  }

  // Determine language from file extension
  const ext = (path.split(".").pop() || "").toLowerCase();
  const langMap = {
    py: "python",
    js: "javascript",
    ts: "typescript",
    jsx: "javascript",
    tsx: "typescript",
    cpp: "cpp",
    cc: "cpp",
    cxx: "cpp",
    c: "cpp",
    h: "cpp",
    hpp: "cpp",
    java: "java",
    rs: "rust",
    go: "go",
    html: "html",
    htm: "html",
    css: "css",
    json: "json",
    md: "markdown",
    sql: "sql",
  };
  const language = langMap[ext] || "text";

  // Switch to split layout
  const chatPage = document.getElementById("chat-page");
  chatPage.classList.add("split-layout");

  // Create wrapper for the panel
  const wrapper = document.createElement("div");
  wrapper.className = "code-review-panel-wrapper";
  chatPage.appendChild(wrapper);

  // Create panel
  const panel = new CodeReviewPanel(
    wrapper,
    path,
    originalText,
    aiContent,
    language,
  );

  panel.onApprove(async (finalContent) => {
    try {
      await fetchWithAuth("/api/write_file", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path, content: finalContent }),
      });
      await fetchWithAuth("/api/confirm_tool", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          confirm_id: confirmId,
          approved: true,
          final_content: finalContent,
        }),
      });
    } catch (err) {
      console.error("Failed to write/confirm file:", err);
    }
    // Trigger slide-out animation, then clean up
    wrapper.classList.add("closing");
    setTimeout(() => {
      panel.destroy();
      chatPage.classList.remove("split-layout");
      wrapper.remove();
    }, 250);
  });

  panel.onReject(async () => {
    try {
      await fetchWithAuth("/api/confirm_tool", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          confirm_id: confirmId,
          approved: false,
        }),
      });
    } catch (err) {
      console.error("Failed to reject:", err);
    }
    // Trigger slide-out animation, then clean up
    wrapper.classList.add("closing");
    setTimeout(() => {
      panel.destroy();
      chatPage.classList.remove("split-layout");
      wrapper.remove();
    }, 250);
  });
}

/**
 * CodeReviewPanel - A CodeMirror 5 based code review panel with diff view.
 */
class CodeReviewPanel {
  /**
   * @param {HTMLElement} container
   * @param {string} path
   * @param {string} originalText
   * @param {string} modifiedText
   * @param {string} language
   */
  constructor(container, path, originalText, modifiedText, language) {
    this.container = container;
    this.path = path;
    this.originalText = originalText;
    this.modifiedText = modifiedText;
    this.language = this._mapLanguage(language);
    this.currentMode = "view";
    this._approveCallback = null;
    this._rejectCallback = null;
    // Store per-line gutter markers so we can clear them later
    this._gutterMarkers = [];
    this._init();
  }

  /**
   * Map file extension language to CodeMirror 5 mode.
   * @param {string} lang
   * @returns {string|object}
   */
  _mapLanguage(lang) {
    if (lang === "cpp" || lang === "cc" || lang === "cxx" || lang === "hpp") {
      return { name: "clike", language: "cpp" };
    }
    if (lang === "c" || lang === "h") {
      return { name: "clike", language: "c" };
    }
    if (lang === "java") {
      return { name: "clike", language: "java" };
    }

    const map = {
      python: "python",
      javascript: "javascript",
      typescript: "javascript",
      rust: "rust",
      go: "go",
      html: "htmlmixed",
      htm: "htmlmixed",
      css: "css",
      json: "javascript",
      markdown: "markdown",
      sql: "sql",
    };
    return map[lang] || "python";
  }

  _init() {
    try {
      // DOM
      this.panelDiv = document.createElement("div");
      this.panelDiv.className = "code-review-panel";

      this.headerDiv = document.createElement("div");
      this.headerDiv.className = "code-review-header";
      this.headerDiv.textContent = this.path || "(unknown file)";

      this.editorDiv = document.createElement("div");
      this.editorDiv.className = "code-review-editor";
      this.editorDiv.style.position = "relative";

      this.footerDiv = document.createElement("div");
      this.footerDiv.className = "code-review-footer";

      const approveBtn = document.createElement("button");
      approveBtn.className = "confirm-approve";
      approveBtn.textContent =
        (typeof t !== "undefined" && t("tool.approve")) || "\u2713 Approve";
      const rejectBtn = document.createElement("button");
      rejectBtn.className = "confirm-reject";
      rejectBtn.textContent =
        (typeof t !== "undefined" && t("tool.reject")) || "\u2717 Reject";

      this.footerDiv.appendChild(approveBtn);
      this.footerDiv.appendChild(rejectBtn);

      this.modeToggleBtn = document.createElement("button");
      this.modeToggleBtn.className = "mode-toggle-btn";
      this.modeToggleBtn.textContent = "\u270E";
      this.modeToggleBtn.title = "Switch to edit mode";

      this.panelDiv.appendChild(this.headerDiv);
      this.panelDiv.appendChild(this.editorDiv);
      this.panelDiv.appendChild(this.footerDiv);
      this.panelDiv.appendChild(this.modeToggleBtn);
      this.container.appendChild(this.panelDiv);

      this.cm = CodeMirror(this.editorDiv, {
        value: this.modifiedText,
        mode: this.language,
        theme: "default",
        lineNumbers: true,
        readOnly: true,
        lineWrapping: true,
        viewportMargin: Infinity,
      });

      this.cm.refresh();

      // Delay diff application to ensure CodeMirror is fully initialised
      setTimeout(() => {
        if (this.cm) {
          this._applyDiff();
        }
      }, 200);

      this.modeToggleBtn.addEventListener("click", () => {
        if (this.currentMode === "view") {
          this.currentMode = "edit";
          this.cm.setOption("readOnly", false);
          this._clearDiff();
          this.modeToggleBtn.textContent = "\uD83D\uDC41";
          this.modeToggleBtn.title = "Switch to view mode";
        } else {
          this.currentMode = "view";
          this.cm.setOption("readOnly", true);
          this._applyDiff();
          this.modeToggleBtn.textContent = "\u270E";
          this.modeToggleBtn.title = "Switch to edit mode";
        }
      });

      approveBtn.addEventListener("click", () => {
        if (this._approveCallback) {
          this._approveCallback(this.cm.getValue());
        }
      });
      rejectBtn.addEventListener("click", () => {
        if (this._rejectCallback) {
          this._rejectCallback();
        }
      });
    } catch (initError) {
      console.error("CodeReviewPanel init failed:", initError);
      this.panelDiv = document.createElement("div");
      this.panelDiv.className = "code-review-panel";
      this.panelDiv.innerHTML =
        '<div class="code-review-header">Initialization failed</div>' +
        '<div class="code-review-editor" style="padding:1rem;color:#dc2626;">' +
        "Error: " +
        initError.message +
        "</div>";
      this.container.appendChild(this.panelDiv);
      this.cm = null;
    }
  }

  /**
   * Apply diff highlights and custom line numbers.
   * Green for additions, red for deletions.
   */
  _applyDiff() {
    if (!this.cm || typeof Diff === "undefined" || !Diff.diffLines) return;

    // Clear previous gutter markers
    this._clearGutterMarkers();

    const currentText = this.cm.getValue();
    const diffResult = Diff.diffLines(this.originalText, currentText);

    const wasReadOnly = this.cm.getOption("readOnly");
    if (wasReadOnly) this.cm.setOption("readOnly", false);

    try {
      let lineOffset = 0; // Current line in the editor
      let origLine = 1; // Line number in the original file
      let newLine = 1; // Line number in the new file

      for (const part of diffResult) {
        const content = part.value;
        const hasTrailingNewline = content.endsWith("\n");
        const lines = content.split("\n");
        const lineCount = hasTrailingNewline ? lines.length - 1 : lines.length;

        if (part.added) {
          // Added lines: green background + green gutter
          for (let i = 0; i < lineCount; i++) {
            const editorLine = lineOffset + i;
            this.cm.addLineClass(editorLine, "background", "cm-diff-insert");
            this.cm.addLineClass(editorLine, "gutter", "cm-diff-insert-gutter");
            // Custom line number: show new file line number, empty for old
            this._setGutterMarker(editorLine, `${newLine + i}`);
          }
          lineOffset += lineCount;
          newLine += lineCount;
        } else if (part.removed) {
          // Deleted lines: insert the original code as placeholders, then mark red
          const removedCode = hasTrailingNewline
            ? lines.slice(0, -1).join("\n")
            : content;
          this.cm.replaceRange(removedCode + "\n", { line: lineOffset, ch: 0 });
          for (let i = 0; i < lineCount; i++) {
            const editorLine = lineOffset + i;
            this.cm.addLineClass(
              editorLine,
              "background",
              "cm-diff-placeholder",
            );
            this.cm.addLineClass(editorLine, "background", "cm-diff-delete");
            this.cm.addLineClass(editorLine, "gutter", "cm-diff-delete-gutter");
            // Custom line number: show original file line number, empty for new
            this._setGutterMarker(editorLine, `${origLine + i}`);
          }
          lineOffset += lineCount;
          origLine += lineCount;
        } else {
          // Unchanged lines: show both line numbers
          for (let i = 0; i < lineCount; i++) {
            const editorLine = lineOffset + i;
            this._setGutterMarker(editorLine, `${newLine + i}`);
          }
          lineOffset += lineCount;
          origLine += lineCount;
          newLine += lineCount;
        }
      }
    } finally {
      if (wasReadOnly) this.cm.setOption("readOnly", true);
    }
    this.editorDiv.classList.add("cm-preview-mode");
  }

  /**
   * Set a custom text in the line-number gutter for a specific line.
   * @param {number} line - 0‑based line index
   * @param {string} text - The text to display (e.g., "12 / " or " / 15")
   */
  _setGutterMarker(line, text) {
    if (!this.cm) return;
    const marker = document.createElement("div");
    marker.className = "custom-linenumber";
    marker.textContent = text;
    this.cm.setGutterMarker(line, "CodeMirror-linenumbers", marker);
    this._gutterMarkers.push(line);
  }

  /**
   * Remove all custom gutter markers that were previously added.
   */
  _clearGutterMarkers() {
    if (!this.cm) return;
    for (const line of this._gutterMarkers) {
      this.cm.setGutterMarker(line, "CodeMirror-linenumbers", null);
    }
    this._gutterMarkers = [];
  }

  /**
   * Remove all diff decorations and gutter markers.
   */
  _clearDiff() {
    if (!this.cm) return;

    // Remove all placeholder lines that were inserted for deleted code
    const linesToRemove = [];
    const lineCount = this.cm.lineCount();
    for (let i = 0; i < lineCount; i++) {
      const classes = this.cm.lineInfo(i).bgClass || "";
      if (classes.includes("cm-diff-placeholder")) {
        linesToRemove.push(i);
      }
    }
    // Remove from bottom to top to keep line indices valid
    for (let i = linesToRemove.length - 1; i >= 0; i--) {
      const line = linesToRemove[i];
      this.cm.replaceRange("", { line, ch: 0 }, { line: line + 1, ch: 0 });
    }

    // Clear all remaining diff-related classes and gutter markers
    const currentLineCount = this.cm.lineCount();
    for (let i = 0; i < currentLineCount; i++) {
      this.cm.removeLineClass(i, "background", "cm-diff-insert");
      this.cm.removeLineClass(i, "background", "cm-diff-delete");
      this.cm.removeLineClass(i, "background", "cm-diff-placeholder");
      this.cm.removeLineClass(i, "gutter", "cm-diff-insert-gutter");
      this.cm.removeLineClass(i, "gutter", "cm-diff-delete-gutter");
    }

    // Clear custom gutter markers
    this._clearGutterMarkers();
    this.editorDiv.classList.remove("cm-preview-mode");
  }

  /**
   * Switch between view and edit modes.
   * @param {string} mode - "view" or "edit"
   */
  setMode(mode) {
    if (mode === this.currentMode || !this.cm) return;

    if (mode === "edit") {
      this.cm.setOption("readOnly", false);
      this._clearDiff();
      this.currentMode = "edit";
      this.modeToggleBtn.textContent = "\uD83D\uDC41";
      this.modeToggleBtn.title = "Switch to view mode";
    } else {
      this.cm.setOption("readOnly", true);
      this._applyDiff();
      this.currentMode = "view";
      this.modeToggleBtn.textContent = "\u270E";
      this.modeToggleBtn.title = "Switch to edit mode";
    }
  }

  /**
   * Register callback for approval.
   * @param {(finalContent: string) => void} cb
   */
  onApprove(cb) {
    this._approveCallback = cb;
  }

  /**
   * Register callback for rejection.
   * @param {() => void} cb
   */
  onReject(cb) {
    this._rejectCallback = cb;
  }

  /**
   * Safely destroy the CodeMirror instance and remove the panel from the DOM.
   */
  destroy() {
    if (this.cm) {
      try {
        this.cm.toTextArea();
      } catch (e) {
        console.warn("CodeMirror toTextArea failed, cleaning up manually.", e);
        const wrapper = this.cm.getWrapperElement();
        if (wrapper && wrapper.parentNode) {
          wrapper.parentNode.removeChild(wrapper);
        }
      }
      this.cm = null;
    }
    if (this.panelDiv && this.panelDiv.parentElement) {
      this.panelDiv.remove();
    }
  }
}
