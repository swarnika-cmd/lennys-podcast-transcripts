const API_BASE = "http://localhost:8000";

// State
let activeSessionId = null;
let currentProvider = "ollama";
let currentMode = "standard";
let activeArtifact = { type: null, title: "Untitled", content: "" };

// DOM Elements
const dbStatusDot = document.getElementById("db-status-dot");
const dbStatusText = document.getElementById("db-status-text");
const btnNewChat = document.getElementById("btn-new-chat");
const sessionsList = document.getElementById("sessions-list");
const providerSelect = document.getElementById("provider-select");
const chatHeaderTitle = document.getElementById("chat-header-title");
const modeStandardBtn = document.getElementById("mode-standard-btn");
const modeEssayBtn = document.getElementById("mode-essay-btn");
const messagesContainer = document.getElementById("messages-container");
const chatInput = document.getElementById("chat-input");
const btnSend = document.getElementById("btn-send");

// Artifact DOM Elements
const artifactPanel = document.getElementById("artifact-panel");
const artifactTypeLabel = document.getElementById("artifact-type-label");
const artifactTitleText = document.getElementById("artifact-title-text");
const tabPreviewBtn = document.getElementById("tab-preview-btn");
const tabCodeBtn = document.getElementById("tab-code-btn");
const btnCloseArtifact = document.getElementById("btn-close-artifact");
const artifactTabPreview = document.getElementById("artifact-tab-preview");
const artifactTabCode = document.getElementById("artifact-tab-code");
const artifactIframe = document.getElementById("artifact-iframe");
const artifactRawCode = document.getElementById("artifact-raw-code");

// Initialize Lucide Icons
lucide.createIcons();

// --- Initialization & Health Check ---
async function checkHealth() {
    try {
        const resp = await fetch(`${API_BASE}/health`);
        const data = await resp.json();
        
        if (data.status === "healthy" && data.database === "connected") {
            dbStatusDot.className = "status-dot connected";
            dbStatusText.innerText = "ONLINE";
        } else {
            dbStatusDot.className = "status-dot";
            dbStatusText.innerText = "DB ERROR";
        }
    } catch (e) {
        dbStatusDot.className = "status-dot";
        dbStatusText.innerText = "OFFLINE";
    }
}

// Initial checks
checkHealth();
setInterval(checkHealth, 10000); // Check health every 10s

// --- Session Handlers ---
async function loadSessions() {
    try {
        const resp = await fetch(`${API_BASE}/sessions`);
        const sessions = await resp.json();
        
        sessionsList.innerHTML = "";
        sessions.forEach(session => {
            const el = document.createElement("div");
            el.className = `session-item ${session.id === activeSessionId ? 'active' : ''}`;
            
            // Format timestamp
            const date = new Date(session.created_at);
            const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            // Use metadata details for title if available
            const title = session.metadata?.title || `Session ${session.id.substring(0, 8)}`;
            
            el.innerHTML = `
                <div class="session-title">${title}</div>
                <div class="session-meta">${date.toLocaleDateString()} @ ${timeStr}</div>
            `;
            
            el.onclick = () => selectSession(session.id);
            sessionsList.appendChild(el);
        });
    } catch (e) {
        console.error("Failed to load sessions:", e);
    }
}

async function startNewSession() {
    try {
        const titlePrompt = prompt("Enter a title for this session:", "Growth Strategy Discussion");
        if (titlePrompt === null) return; // cancelled
        
        const resp = await fetch(`${API_BASE}/sessions`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                metadata: { title: titlePrompt || "New Session" }
            })
        });
        
        const newSession = await resp.json();
        activeSessionId = newSession.id;
        chatHeaderTitle.innerText = newSession.metadata?.title || "Active Session";
        
        // Clear messages container (leave system intro)
        messagesContainer.innerHTML = "";
        appendSystemMessage("SYSTEM // NEW SESSION INIT", "New conversation session initialized successfully. Ask anything grounded in the podcast transcripts.");
        
        await loadSessions();
        chatInput.focus();
    } catch (e) {
        alert("Failed to start new session. Make sure backend is running.");
    }
}

async function selectSession(sessionId) {
    activeSessionId = sessionId;
    // Highlight session in sidebar
    loadSessions();
    
    try {
        const resp = await fetch(`${API_BASE}/sessions/${sessionId}`);
        const session = await resp.json();
        
        chatHeaderTitle.innerText = session.metadata?.title || "Active Session";
        messagesContainer.innerHTML = "";
        
        if (session.messages && session.messages.length > 0) {
            session.messages.forEach(msg => {
                appendMessageBubble(msg.role, msg.content, msg.citations, false);
            });
        } else {
            appendSystemMessage("SYSTEM // EMPTY SESSION", "This session contains no previous messages. Start the conversation below.");
        }
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } catch (e) {
        console.error("Failed to load session messages:", e);
    }
}

// --- Message Rendering Helpers ---
function appendSystemMessage(meta, text) {
    const wrapper = document.createElement("div");
    wrapper.className = "message-wrapper assistant";
    wrapper.innerHTML = `
        <div class="message-meta">${meta}</div>
        <div class="message-bubble">${marked.parse(text)}</div>
    `;
    messagesContainer.appendChild(wrapper);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function appendMessageBubble(role, content, citations = [], animate = true) {
    const wrapper = document.createElement("div");
    wrapper.className = `message-wrapper ${role}`;
    
    const metaText = role === "user" ? "USER // IN" : "ASSISTANT // OUT";
    
    // Parse Markdown safely
    const parsedText = marked.parse(content);
    
    let bubbleHtml = `<div class="message-bubble">${parsedText}`;
    
    // Check for HTML/Markdown code blocks to turn them into artifacts
    const htmlArtifact = detectHtmlArtifact(content);
    const mdArtifact = detectMarkdownArtifact(content);
    
    if (htmlArtifact) {
        bubbleHtml += `
            <div class="artifact-button-wrapper">
                <button class="btn-open-artifact" onclick="openArtifact('html', '${htmlArtifact.title}', \`${escapeCode(htmlArtifact.code)}\`)">
                    <i data-lucide="layout" style="width:14px; height:14px;"></i>
                    <span>Render HTML Page</span>
                </button>
            </div>
        `;
    } else if (mdArtifact) {
        bubbleHtml += `
            <div class="artifact-button-wrapper">
                <button class="btn-open-artifact" onclick="openArtifact('markdown', '${mdArtifact.title}', \`${escapeCode(mdArtifact.code)}\`)">
                    <i data-lucide="file-text" style="width:14px; height:14px;"></i>
                    <span>Preview Document</span>
                </button>
            </div>
        `;
    }
    
    // Append citations if available
    if (role === "assistant" && citations && citations.length > 0) {
        bubbleHtml += `
            <div class="citations-box">
                <div class="citation-title">Grounded Sources</div>
                <div class="citation-links">
        `;
        
        citations.forEach(c => {
            const cleanUrl = c.youtube_url || `https://youtube.com/watch?v=${c.video_id}`;
            bubbleHtml += `
                <a href="${cleanUrl}" target="_blank" class="citation-link">
                    <i data-lucide="external-link" style="width:10px; height:10px;"></i>
                    <span>${c.guest} - ${c.title.substring(0, 30)}... [Chunk ${c.chunk_index}]</span>
                </a>
            `;
        });
        
        bubbleHtml += `
                </div>
            </div>
        `;
    }
    
    bubbleHtml += `</div>`;
    
    wrapper.innerHTML = `
        <div class="message-meta">${metaText}</div>
        ${bubbleHtml}
    `;
    
    messagesContainer.appendChild(wrapper);
    lucide.createIcons(); // Instantiates icons inside citation links
    
    if (animate) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Helpers for Artifact Extraction
function detectHtmlArtifact(text) {
    const htmlRegex = /```html\s*([\s\S]*?)```/i;
    const match = text.match(htmlRegex);
    if (match) {
        // Try to extract a title from H1 or Title tags, otherwise default
        const titleMatch = match[1].match(/<title>([\s\S]*?)<\/title>/i) || match[1].match(/<h1>([\s\S]*?)<\/h1>/i);
        const title = titleMatch ? titleMatch[1].trim() : "Interactive Web Page";
        return { title, code: match[1] };
    }
    return null;
}

function detectMarkdownArtifact(text) {
    // Look for generic markdown code block
    const mdRegex = /```markdown\s*([\s\S]*?)```/i;
    const match = text.match(mdRegex);
    if (match) {
        const firstLine = match[1].split("\n")[0] || "";
        const title = firstLine.startsWith("#") ? firstLine.replace("#", "").trim() : "Markdown Document";
        return { title, code: match[1] };
    }
    return null;
}

function escapeCode(code) {
    return code
        .replace(/\\/g, '\\\\')
        .replace(/`/g, '\\`')
        .replace(/\${/g, '\\${');
}

// --- Artifact Viewer Logic ---
window.openArtifact = function(type, title, code) {
    activeArtifact = { type, title, content: code };
    
    // UI details
    artifactTypeLabel.innerText = type === "html" ? "Rendered HTML Artifact" : "Markdown Preview";
    artifactTitleText.innerText = title;
    
    // Code tab content
    artifactRawCode.innerText = code;
    
    // Preview tab content (Iframe sandbox injection)
    if (type === "html") {
        artifactIframe.srcdoc = code;
    } else {
        // Render Markdown inside iframe
        const renderedHtml = marked.parse(code);
        artifactIframe.srcdoc = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                        line-height: 1.6;
                        color: #1a1f26;
                        padding: 30px;
                        max-width: 800px;
                        margin: 0 auto;
                        background: #fbfcfd;
                    }
                    h1, h2, h3 {
                        color: #0b0d10;
                        margin-top: 24px;
                        font-weight: 700;
                    }
                    h1 { border-bottom: 2px solid #e3e6eb; padding-bottom: 8px; font-size: 28px; }
                    h2 { border-bottom: 1px solid #e3e6eb; padding-bottom: 6px; font-size: 22px; }
                    pre {
                        background: #f1f3f5;
                        padding: 16px;
                        border-radius: 4px;
                        overflow-x: auto;
                        border: 1px solid #e3e6eb;
                    }
                    code {
                        font-family: monospace;
                        background: #f1f3f5;
                        padding: 2px 4px;
                        border-radius: 3px;
                        font-size: 13px;
                    }
                    blockquote {
                        border-left: 4px solid #00e5ff;
                        padding-left: 16px;
                        color: #5b6573;
                        font-style: italic;
                        margin: 16px 0;
                    }
                    ul, ol { margin-left: 24px; margin-bottom: 16px; }
                    li { margin-bottom: 6px; }
                </style>
            </head>
            <body>
                ${renderedHtml}
            </body>
            </html>
        `;
    }
    
    // Switch to preview tab by default
    switchTab("preview");
    
    // Slide open panel
    artifactPanel.classList.add("open");
};

function switchTab(tab) {
    if (tab === "preview") {
        tabPreviewBtn.classList.add("active");
        tabCodeBtn.classList.remove("active");
        artifactTabPreview.classList.add("active");
        artifactTabCode.classList.remove("active");
    } else {
        tabPreviewBtn.classList.remove("active");
        tabCodeBtn.classList.add("active");
        artifactTabPreview.classList.remove("active");
        artifactTabCode.classList.add("active");
    }
}

// Close Artifact Panel
btnCloseArtifact.onclick = () => {
    artifactPanel.classList.remove("open");
};

tabPreviewBtn.onclick = () => switchTab("preview");
tabCodeBtn.onclick = () => switchTab("code");

// --- API Message Sender ---
async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    
    if (!activeSessionId) {
        alert("Please create or select a chat session first using the sidebar!");
        return;
    }
    
    // Append user message bubble
    appendMessageBubble("user", text);
    chatInput.value = "";
    
    // Disable inputs while loading
    chatInput.disabled = true;
    btnSend.disabled = true;
    
    // Append loading assistant bubble
    const loaderWrapper = document.createElement("div");
    loaderWrapper.className = "message-wrapper assistant loader-bubble";
    loaderWrapper.innerHTML = `
        <div class="message-meta">SYSTEM // GENERATING</div>
        <div class="message-bubble" style="font-family: var(--font-mono); font-size:12px; color: var(--accent-cyan);">
            SEARCHING VECTOR EMBEDDINGS & RUNNING COGNITIVE ROUTER...
        </div>
    `;
    messagesContainer.appendChild(loaderWrapper);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    try {
        const resp = await fetch(`${API_BASE}/sessions/${activeSessionId}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: text,
                provider: currentProvider,
                mode: currentMode
            })
        });
        
        // Remove loader bubble
        const loader = document.querySelector(".loader-bubble");
        if (loader) loader.remove();
        
        if (!resp.ok) {
            const errorData = await resp.json();
            throw new Error(errorData.detail || "Server error");
        }
        
        const data = await resp.json();
        
        // Append response
        appendMessageBubble("assistant", data.content, data.citations);
    } catch (e) {
        const loader = document.querySelector(".loader-bubble");
        if (loader) loader.remove();
        
        appendMessageBubble("assistant", `❌ **API Generation Failed:** ${e.message}`, []);
    } finally {
        chatInput.disabled = false;
        btnSend.disabled = false;
        chatInput.focus();
    }
}

// --- Bindings ---
btnSend.onclick = sendMessage;
chatInput.onkeydown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
};

btnNewChat.onclick = startNewSession;

providerSelect.onchange = (e) => {
    currentProvider = e.target.value;
};

// Mode Buttons
modeStandardBtn.onclick = () => {
    currentMode = "standard";
    modeStandardBtn.className = "mode-btn active";
    modeEssayBtn.className = "mode-btn";
};

modeEssayBtn.onclick = () => {
    currentMode = "essay";
    modeStandardBtn.className = "mode-btn";
    modeEssayBtn.className = "mode-btn active";
};

// Load sessions initially
loadSessions();
