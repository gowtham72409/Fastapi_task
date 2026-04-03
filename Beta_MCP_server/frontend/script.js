/* ── TalkBuddy — script.js ─────────────────────────────────── */

const WS_URL     = "ws://localhost:8000/ws";
const MIC_WS_URL = "ws://localhost:8000/ws/mic";
const API_URL    = "http://localhost:8000";

// ── DOM refs ──────────────────────────────────────────────────
const chat         = document.getElementById("chat");
const msgInput     = document.getElementById("msgInput");
const connBadge    = document.getElementById("connBadge");
const wsDot        = document.getElementById("wsStatus");
const waveBar      = document.getElementById("waveformBar");
const micBtn       = document.getElementById("micBtn");
const waveCanvas   = document.getElementById("waveCanvas");
const micTimer     = document.getElementById("micTimer");
const mcpPanel     = document.getElementById("mcpPanel");
const mcpTools     = document.getElementById("mcpTools");
const activePills  = document.getElementById("activePills");
const pdfBanner    = document.getElementById("pdfBanner");
const pdfBannerTxt = document.getElementById("pdfBannerText");
const appShell     = document.getElementById("appShell");
const chatContainer= document.getElementById("chatContainer");
const attMenu      = document.getElementById("attMenu");
const historyList  = document.getElementById("historyList");

// ── Session History ───────────────────────────────────────────
// Each session: { id, title, messages: [{role:'user'|'bot', html, tagsHtml}] }
let sessions       = [];     // all saved sessions
let activeSession  = null;   // currently open session object (or null = fresh)

function _makeSession(title) {
  return { id: Date.now(), title, messages: [] };
}

function _saveCurrentToHistory() {
  if (!activeSession || activeSession.messages.length === 0) return;
  // Update if it already exists in sessions array, otherwise push
  const idx = sessions.findIndex(s => s.id === activeSession.id);
  if (idx >= 0) sessions[idx] = activeSession;
  else sessions.unshift(activeSession);
  renderHistory();
}

function renderHistory() {
  const today = new Date().toDateString();
  const todayItems   = sessions.filter(s => new Date(s.id).toDateString() === today);
  const olderItems   = sessions.filter(s => new Date(s.id).toDateString() !== today);

  let html = "";
  if (todayItems.length) {
    html += `<div class="history-label">Today</div>`;
    todayItems.forEach(s => {
      html += `<div class="history-item${activeSession?.id === s.id ? " active-session" : ""}" 
                    onclick="loadSession(${s.id})" 
                    title="${escHtml(s.title)}">
                 ${escHtml(s.title.length > 32 ? s.title.slice(0, 32) + "…" : s.title)}
               </div>`;
    });
  }
  if (olderItems.length) {
    html += `<div class="history-label" style="margin-top:14px">Earlier</div>`;
    olderItems.forEach(s => {
      html += `<div class="history-item${activeSession?.id === s.id ? " active-session" : ""}" 
                    onclick="loadSession(${s.id})"
                    title="${escHtml(s.title)}">
                 ${escHtml(s.title.length > 32 ? s.title.slice(0, 32) + "…" : s.title)}
               </div>`;
    });
  }
  if (!sessions.length) {
    html = `<div style="font-size:12px;color:#4b5563;padding:12px 0">No history yet</div>`;
  }

  historyList.innerHTML = html;
}

function loadSession(id) {
  // Save current first
  _saveCurrentToHistory();

  const session = sessions.find(s => s.id === id);
  if (!session) return;

  // Switch to this session
  activeSession = session;
  chat.innerHTML = "";

  session.messages.forEach(m => {
    const el = document.createElement("div");
    el.className = "msg " + m.role;
    el.innerHTML = m.html;
    chat.appendChild(el);
  });

  startChat();    // move input to bottom
  scrollBottom();
  renderHistory();
}

// ── UI State helpers ──────────────────────────────────────────
function toggleSidebar()      { appShell.classList.toggle("sidebar-open"); }
function toggleAttachmentMenu() { attMenu.classList.toggle("open"); }

function startChat() {
  chatContainer.classList.remove("chat-empty");
  // Start a session if we don't have one active
  if (!activeSession) {
    activeSession = _makeSession("New Chat");
  }
}

function newChat() {
  _saveCurrentToHistory();
  activeSession = null;
  chat.innerHTML = "";
  clearPdf();
  chatContainer.classList.add("chat-empty");
  msgInput.placeholder = "Message the agents…";
  activePills.innerHTML = "";
  renderHistory();
}

// Close attachment menu when clicking outside
document.addEventListener("click", (e) => {
  const wrapper = document.getElementById("attachmentWrapper");
  if (wrapper && !wrapper.contains(e.target)) attMenu.classList.remove("open");
});

// ── PDF state ─────────────────────────────────────────────────
let pdfContext  = "";
let pdfFilename = "";

function shouldUsePdf() { return !!pdfContext; }

// ── WebSocket ─────────────────────────────────────────────────
let ws;
function connectWS() {
  ws = new WebSocket(WS_URL);
  ws.onopen  = () => setConnState("ok");
  ws.onmessage = (evt) => { removeTyping(); renderBotResponse(JSON.parse(evt.data)); };
  ws.onclose = () => { setConnState("err"); setTimeout(connectWS, 2500); };
  ws.onerror = () => setConnState("err");
}
connectWS();

function setConnState(s) {
  connBadge.textContent = s === "ok" ? "●" : "●";
  connBadge.className   = "conn-badge " + (s === "ok" ? "ok" : "err");
  wsDot.className       = "status-dot " + (s === "ok" ? "connected" : "error");
}

// ── Send message ──────────────────────────────────────────────
function sendMessage() {
  const text = msgInput.value.trim();
  if (!text) return;
  msgInput.value = "";
  startChat();

  if (shouldUsePdf()) {
    sendPdfQuestion(text);
  } else {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      addBotMessage("⚠ Not connected. Please wait…"); return;
    }
    addUserMessage(text);
    showTyping();
    ws.send(text);
  }
}

msgInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

// ── PDF Q&A via REST ──────────────────────────────────────────
async function sendPdfQuestion(question) {
  addUserMessage(question);
  showTyping();

  try {
    const res = await fetch(`${API_URL}/ask-pdf`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, pdf_text: pdfContext.slice(0, 12000) }),
    });

    if (!res.ok) { throw new Error(`Server ${res.status}: ${await res.text()}`); }
    const data = await res.json();
    removeTyping();

    if (data.type === "not_in_pdf") {
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        addBotMessage("⚠ Not connected. Cannot perform agent search.");
        return;
      }
      showTyping();
      ws.send(question);
    } else if (data.type === "agent_answer") {
      renderBotResponse(data);
    } else {
      renderPdfAnswer(data.answer || data.chat || "(no response)");
    }

  } catch (err) {
    removeTyping();
    addBotMessage(`⚠ PDF Q&A failed: ${err.message}`);
  }
}

// ── Render helpers ────────────────────────────────────────────
function renderPdfAnswer(text) {
  const srcMatch = text.match(/Sources\s*:\s*([^\n]+)$/im);
  let mainText = text, pages = [];
  if (srcMatch) {
    mainText = text.slice(0, srcMatch.index).trim();
    pages = srcMatch[1].split(",").map(s => s.trim().replace(/^page\s*/i, "Page ")).filter(Boolean);
  }

  const innerHtml = `
    <div class="msg-bubble">${formatResponse(mainText)}</div>
    ${pages.length ? `
      <div class="page-sources">
        <span class="sources-label">Sources</span>
        ${pages.map(p => `<span class="page-badge">📄 ${p}</span>`).join("")}
      </div>` : ""}
    <div class="msg-meta"><span class="meta-tag pdf">PDF Answer</span></div>`;

  _appendMsg("bot", innerHtml);
}

function addUserMessage(text, tags = []) {
  const tagsHtml = tags.map(t => `<span class="meta-tag ${t.cls}">${t.label}</span>`).join("");
  const innerHtml = `<div class="msg-bubble">${escHtml(text)}</div>` +
                    (tagsHtml ? `<div class="msg-meta">${tagsHtml}</div>` : "");

  // Set session title from first user message — must run BEFORE _appendMsg pushes to messages
  if (activeSession && activeSession.messages.filter(m => m.role === "user").length === 0) {
    activeSession.title = text.length > 40 ? text.slice(0, 40) + "…" : text;
  }

  _appendMsg("user", innerHtml);
}

function addBotMessage(text, tags = []) {
  const innerHtml = `<div class="msg-bubble">${formatResponse(text)}</div>` ;
  _appendMsg("bot", innerHtml);
}

function renderBotResponse(data) {
  const tags = [];
  if (data.cached)              tags.push({ cls: "cache", label: "⚡ Cached" });
  if (data.mcp)                 tags.push({ cls: "mcp",   label: "MCP" });
  if (data.results?.code)       tags.push({ cls: "code",  label: "Code" });
  if (data.results?.research)   tags.push({ cls: "",      label: "Research" });
  updatePills(data.results || {});
  addBotMessage(data.chat || data.answer || "(no response)", tags);
}

function _appendMsg(role, innerHtml) {
  const el = document.createElement("div");
  el.className = "msg " + role;
  el.innerHTML = innerHtml;
  chat.appendChild(el);
  scrollBottom();

  // Save to active session
  if (activeSession) {
    activeSession.messages.push({ role, html: innerHtml });
    _saveCurrentToHistory();  // persist on every message
  }
}

function updatePills(results) {
  activePills.innerHTML = Object.keys(results)
    .map(a => `<span class="pill active">${a}</span>`).join("");
}

function showTyping() {
  if (document.getElementById("typingIndicator")) return;
  const el = document.createElement("div");
  el.className = "msg bot typing-indicator";
  el.id = "typingIndicator";
  el.innerHTML = `<div class="msg-bubble"><div class="dots"><span/><span/><span/></div></div>`;
  chat.appendChild(el); scrollBottom();
}
function removeTyping() { document.getElementById("typingIndicator")?.remove(); }
function scrollBottom() { chat.scrollTop = chat.scrollHeight; }

function escHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
function formatResponse(text) {
  return escHtml(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br>");
}

// ── PDF upload ────────────────────────────────────────────────
document.getElementById("pdfFile").addEventListener("change", async function () {
  const file = this.files[0];
  if (!file) return;
  this.value = "";

  startChat();
  attMenu.classList.remove("open");
  addUserMessage(`📄 ${file.name}`, [{ cls: "pdf", label: "PDF" }]);
  showTyping();

  const formData = new FormData();
  formData.append("file", file);
  formData.append("question", "");

  try {
    const res = await fetch(`${API_URL}/upload-pdf`, { method: "POST", body: formData });
    if (!res.ok) throw new Error(`Server ${res.status}: ${await res.text()}`);

    const data = await res.json();
    removeTyping();

    pdfContext  = data.pdf_text || "";
    pdfFilename = file.name;

    showPdfBanner(file.name, data.page_count, data.truncated);
    addBotMessage(
      `✅ **${file.name}** indexed — ${data.page_count} page(s) ready.\nAsk me anything about this document.`,
      [{ cls: "pdf", label: "PDF Indexed" }]
    );
  } catch (err) {
    removeTyping();
    addBotMessage(`⚠ PDF upload failed: ${err.message}`);
  }
});

function showPdfBanner(name, pages, truncated) {
  pdfBannerTxt.textContent =
    `${name} · ${pages} page(s) indexed${truncated ? " · truncated" : ""} · Questions about doc go to PDF · Others go to agents`;
  pdfBanner.style.display = "flex";
  msgInput.placeholder = `Ask about ${name}, or ask anything else…`;
}

function clearPdf() {
  pdfContext  = "";
  pdfFilename = "";
  pdfBanner.style.display = "none";
  msgInput.placeholder = "Message the agents…";
}

// ── Audio / Video upload ──────────────────────────────────────
document.getElementById("audioFile").addEventListener("change", async function () {
  const file = this.files[0]; if (!file) return; this.value = "";
  startChat(); attMenu.classList.remove("open");
  addUserMessage(`🎵 ${file.name}`, [{ cls: "", label: "Audio" }]); showTyping();
  const fd = new FormData(); fd.append("file", file);
  try {
    const data = await (await fetch(`${API_URL}/upload-audio`, { method: "POST", body: fd })).json();
    removeTyping();
    addUserMessage(data.transcript, [{ cls: "mic", label: "Transcribed" }]);
    renderBotResponse(data);
  } catch (err) { removeTyping(); addBotMessage("⚠ Audio failed: " + err.message); }
});

document.getElementById("videoFile").addEventListener("change", async function () {
  const file = this.files[0]; if (!file) return; this.value = "";
  startChat(); attMenu.classList.remove("open");
  addUserMessage(`🎬 ${file.name}`, [{ cls: "", label: "Video" }]); showTyping();
  const fd = new FormData(); fd.append("file", file);
  try {
    const data = await (await fetch(`${API_URL}/upload-video`, { method: "POST", body: fd })).json();
    removeTyping();
    addUserMessage(data.transcript, [{ cls: "mic", label: "Transcribed" }]);
    renderBotResponse(data);
  } catch (err) { removeTyping(); addBotMessage("⚠ Video failed: " + err.message); }
});

// ── Mic ───────────────────────────────────────────────────────
let mediaRecorder = null, micWs = null, audioChunks = [];
let timerInterval = null, timerSec = 0;
let analyser = null, animFrame = null, audioCtx = null;

async function toggleMic() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") stopMic();
  else await startMic();
}

async function startMic() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioCtx = new AudioContext();
    const src = audioCtx.createMediaStreamSource(stream);
    analyser = audioCtx.createAnalyser(); analyser.fftSize = 256;
    src.connect(analyser); drawWave();

    micWs = new WebSocket(MIC_WS_URL);
    micWs.binaryType = "arraybuffer";
    micWs.onmessage = (evt) => {
      const data = JSON.parse(evt.data); removeTyping();
      if (data.type === "transcript") {
        addUserMessage(data.text, [{ cls: "mic", label: "Transcribed" }]); showTyping();
      } else if (data.type === "agent_result") {
        renderBotResponse(data);
        if (micWs) { micWs.close(); micWs = null; }
      }
    };
    micWs.onclose = () => removeTyping();
    micWs.onerror = () => { removeTyping(); addBotMessage("⚠ Mic connection error"); };

    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
    mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data); };
    mediaRecorder.onstop = async () => {
      const blob = new Blob(audioChunks, { type: "audio/webm" }); audioChunks = [];
      startChat();
      if (micWs?.readyState === WebSocket.OPEN) {
        showTyping(); micWs.send(await blob.arrayBuffer());
      }
      stream.getTracks().forEach(t => t.stop());
    };
    mediaRecorder.start();

    micBtn.classList.add("active"); waveBar.classList.add("active");
    timerSec = 0; micTimer.textContent = "0:00";
    timerInterval = setInterval(() => {
      timerSec++;
      micTimer.textContent = `${Math.floor(timerSec / 60)}:${String(timerSec % 60).padStart(2, "0")}`;
    }, 1000);
  } catch (err) { alert("Microphone error: " + err.message); }
}

function stopMic() {
  if (mediaRecorder?.state !== "inactive") mediaRecorder?.stop();
  clearInterval(timerInterval); cancelAnimationFrame(animFrame);
  if (audioCtx) { audioCtx.close(); audioCtx = null; }
  micBtn.classList.remove("active"); waveBar.classList.remove("active");
}

function drawWave() {
  const ctx = waveCanvas.getContext("2d");
  const buf = new Uint8Array(analyser.frequencyBinCount);
  const W = waveCanvas.width, H = waveCanvas.height;
  function render() {
    animFrame = requestAnimationFrame(render);
    analyser.getByteTimeDomainData(buf);
    ctx.clearRect(0, 0, W, H);
    ctx.strokeStyle = "#f5495b"; ctx.lineWidth = 2; ctx.beginPath();
    buf.forEach((v, i) => {
      const x = i * W / buf.length, y = (v / 128) * H / 2;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.lineTo(W, H / 2); ctx.stroke();
  }
  render();
}

// ── MCP Panel ─────────────────────────────────────────────────
function toggleMcpPanel() { if (mcpPanel.classList.toggle("open")) loadMcpTools(); }

async function loadMcpTools() {
  mcpTools.innerHTML = "Loading…";
  try {
    const data = await (await fetch(`${API_URL.replace("8000", "8001")}/mcp/tools`)).json();
    const tools = data.tools || {};
    mcpTools.innerHTML = Object.keys(tools).length
      ? Object.entries(tools).map(([n, i]) => `
          <div class="mcp-tool-card">
            <div class="mcp-tool-name">${n}</div>
            <div class="mcp-tool-desc">${i.description}</div>
            <div class="mcp-provider">${i.provider}</div>
          </div>`).join("")
      : `<span style="color:#4b5563;font-size:12px">No tools registered</span>`;
  } catch {
    mcpTools.innerHTML = `<span style="color:var(--red);font-size:12px">MCP server unreachable</span>`;
  }
}

// ── Init ──────────────────────────────────────────────────────
renderHistory();
