/**
 * AI Research Paper Assistant - Frontend Interaction Logic
 * Author: NewtonCode (Mani Barathi P)
 */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const uploadStatus = document.getElementById("upload-status");
  const uploadStatusText = document.getElementById("upload-status-text");
  const documentsList = document.getElementById("documents-list");
  const indexedCountBadge = document.getElementById("indexed-count-badge");
  const totalChunksInfo = document.getElementById("total-chunks-info");
  const clearDbBtn = document.getElementById("clear-db-btn");
  const geminiStatusBadge = document.getElementById("gemini-status");
  const geminiStatusText = document.getElementById("gemini-status-text");
  
  const chatMessages = document.getElementById("chat-messages");
  const queryForm = document.getElementById("query-form");
  const queryInput = document.getElementById("query-input");
  const sendBtn = document.getElementById("send-btn");
  const clearChatBtn = document.getElementById("clear-chat-btn");
  const promptPills = document.querySelectorAll(".prompt-pill");

  // State
  let isGenerating = false;

  // 1. Initial System Check
  checkSystemHealth();
  refreshDocumentList();

  // 2. Health & Status Check
  async function checkSystemHealth() {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      const dot = geminiStatusBadge.querySelector(".status-dot");

      if (data.gemini_api_configured) {
        dot.className = "status-dot online";
        geminiStatusText.textContent = `Gemini Online (${data.gemini_model})`;
      } else {
        dot.className = "status-dot offline";
        geminiStatusText.textContent = "Gemini Key Not Configured";
      }
    } catch (err) {
      const dot = geminiStatusBadge.querySelector(".status-dot");
      dot.className = "status-dot offline";
      geminiStatusText.textContent = "Server Offline";
    }
  }

  // 3. Document List Refresh
  async function refreshDocumentList() {
    try {
      const res = await fetch("/api/documents");
      const data = await res.json();

      if (!data.success || !data.documents || data.documents.length === 0) {
        documentsList.innerHTML = `
          <div class="empty-state-small">
            <p>No research papers indexed yet.</p>
            <span>Upload a PDF paper above to begin retrieval.</span>
          </div>
        `;
        indexedCountBadge.textContent = "0 documents";
        totalChunksInfo.textContent = "Total chunks: 0";
        return;
      }

      indexedCountBadge.textContent = `${data.documents.length} document${data.documents.length > 1 ? 's' : ''}`;
      totalChunksInfo.textContent = `Total chunks: ${data.total_chunks}`;

      documentsList.innerHTML = data.documents.map(doc => `
        <div class="doc-item">
          <div class="doc-info">
            <span class="doc-title" title="${doc.filename}">${escapeHtml(doc.filename)}</span>
            <span class="doc-meta">${doc.total_pages} page(s) • ${doc.chunk_count} chunk(s)</span>
          </div>
        </div>
      `).join("");
    } catch (err) {
      console.error("Failed to load documents:", err);
    }
  }

  // 4. File Upload Handlers (Drag & Drop + File Picker)
  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFilesUpload(files);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      handleFilesUpload(e.target.files);
    }
  });

  async function handleFilesUpload(files) {
    const formData = new FormData();
    let hasPdf = false;

    for (let i = 0; i < files.length; i++) {
      if (files[i].name.toLowerCase().endsWith(".pdf")) {
        formData.append("files", files[i]);
        hasPdf = true;
      }
    }

    if (!hasPdf) {
      alert("Please select valid PDF research papers.");
      return;
    }

    // Show upload progress
    uploadStatus.classList.remove("hidden");
    uploadStatusText.textContent = `Processing & embedding ${files.length} paper(s)...`;

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data.success) {
        uploadStatusText.textContent = `Indexed ${data.results.length} paper(s) successfully!`;
        setTimeout(() => {
          uploadStatus.classList.add("hidden");
        }, 3000);
        refreshDocumentList();
        appendSystemNotification(`Successfully uploaded and indexed ${data.results.length} paper(s) into ChromaDB.`);
      } else {
        uploadStatusText.textContent = `Upload failed: ${data.error || "Unknown error"}`;
        setTimeout(() => {
          uploadStatus.classList.add("hidden");
        }, 5000);
      }
    } catch (err) {
      uploadStatusText.textContent = "Error communicating with server.";
      setTimeout(() => {
        uploadStatus.classList.add("hidden");
      }, 4000);
    } finally {
      fileInput.value = "";
    }
  }

  // 5. Clear Knowledge Base Handler
  clearDbBtn.addEventListener("click", async () => {
    if (!confirm("Are you sure you want to clear all indexed research papers and reset ChromaDB?")) {
      return;
    }

    try {
      const res = await fetch("/api/clear", { method: "POST" });
      const data = await res.json();
      if (data.success) {
        refreshDocumentList();
        appendSystemNotification("Knowledge base has been cleared.");
      }
    } catch (err) {
      alert("Failed to clear knowledge base: " + err.message);
    }
  });

  // 6. Prompt Pills Click
  promptPills.forEach(pill => {
    pill.addEventListener("click", () => {
      const text = pill.getAttribute("data-query");
      queryInput.value = text;
      autoResizeTextarea(queryInput);
      queryInput.focus();
    });
  });

  // 7. Auto-resize Textarea & Keyboard Handling
  function autoResizeTextarea(textarea) {
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
  }

  queryInput.addEventListener("input", () => {
    autoResizeTextarea(queryInput);
  });

  queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isGenerating && queryInput.value.trim().length > 0) {
        queryForm.dispatchEvent(new Event("submit"));
      }
    }
  });

  // 8. Query Form Submit
  queryForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query || isGenerating) return;

    // Append User Message
    appendUserMessage(query);
    queryInput.value = "";
    autoResizeTextarea(queryInput);

    // Append Assistant Loading Indicator
    const loadingId = appendAssistantLoading();
    isGenerating = true;
    sendBtn.disabled = true;

    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: query, k: 4 }),
      });

      const data = await res.json();
      removeElementById(loadingId);

      if (data.success) {
        appendAssistantMessage(data.answer, data.sources, data.timestamp);
      } else {
        appendAssistantMessage(
          `**Error:** ${data.error || "An error occurred while retrieving answer."}`,
          [],
          data.timestamp || "Now"
        );
      }
    } catch (err) {
      removeElementById(loadingId);
      appendAssistantMessage(`**Connection Error:** Unable to reach the server. (${err.message})`, [], "Now");
    } finally {
      isGenerating = false;
      sendBtn.disabled = false;
      queryInput.focus();
    }
  });

  // 9. Clear Chat
  clearChatBtn.addEventListener("click", () => {
    chatMessages.innerHTML = `
      <div class="message system-welcome">
        <div class="welcome-card">
          <div class="welcome-header">
            <div class="welcome-icon">✨</div>
            <div>
              <h4>Chat History Cleared</h4>
              <p>Ask questions about your uploaded research papers below.</p>
            </div>
          </div>
        </div>
      </div>
    `;
  });

  // DOM Helpers for Chat Messages
  function appendUserMessage(text) {
    const time = formatTime(new Date());
    const row = document.createElement("div");
    row.className = "message-row user";
    row.innerHTML = `
      <div class="avatar user-avatar">U</div>
      <div class="message-bubble">
        <div class="user-text">${escapeHtml(text)}</div>
        <div class="message-meta">${time}</div>
      </div>
    `;
    chatMessages.appendChild(row);
    scrollToBottom();
  }

  function appendAssistantLoading() {
    const tempId = "loading-" + Date.now();
    const row = document.createElement("div");
    row.className = "message-row assistant";
    row.id = tempId;
    row.innerHTML = `
      <div class="avatar ai-avatar">AI</div>
      <div class="message-bubble">
        <div style="display: flex; align-items: center; gap: 0.6rem; color: var(--text-muted); font-size: 0.85rem;">
          <div class="spinner-small"></div>
          <span>Retrieving relevant chunks & synthesizing answer with Gemini...</span>
        </div>
      </div>
    `;
    chatMessages.appendChild(row);
    scrollToBottom();
    return tempId;
  }

  function appendAssistantMessage(rawMarkdown, sources = [], timestamp = "") {
    const time = timestamp || formatTime(new Date());
    const renderedHtml = typeof marked !== "undefined" ? marked.parse(rawMarkdown) : rawMarkdown;

    const row = document.createElement("div");
    row.className = "message-row assistant";

    let sourcesHtml = "";
    if (sources && sources.length > 0) {
      const citationItems = sources.map((s, idx) => `
        <div class="citation-item">
          <div class="citation-header">
            <span class="citation-source">📄 ${escapeHtml(s.document)}</span>
            <span class="citation-page">Page ${s.page}</span>
          </div>
          <div class="citation-snippet">"${escapeHtml(s.snippet)}"</div>
        </div>
      `).join("");

      sourcesHtml = `
        <div class="citations-wrapper">
          <button class="citations-toggle" onclick="this.nextElementSibling.classList.toggle('hidden');">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
            </svg>
            View Retrieved Sources & Citations (${sources.length})
          </button>
          <div class="citations-list">
            ${citationItems}
          </div>
        </div>
      `;
    }

    row.innerHTML = `
      <div class="avatar ai-avatar">AI</div>
      <div class="message-bubble">
        <div class="markdown-body">${renderedHtml}</div>
        ${sourcesHtml}
        <div class="message-meta">AI Assistant • ${time}</div>
      </div>
    `;

    chatMessages.appendChild(row);
    scrollToBottom();
  }

  function appendSystemNotification(text) {
    const div = document.createElement("div");
    div.style.cssText = "text-align: center; color: var(--text-dim); font-size: 0.74rem; margin: 0.4rem 0;";
    div.textContent = `ℹ️ ${text}`;
    chatMessages.appendChild(div);
    scrollToBottom();
  }

  function removeElementById(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function formatTime(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function escapeHtml(text) {
    if (!text) return "";
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
