/* ── TalkBuddy — script.js ─────────────────────────────────── */

const WS_URL     = "ws://localhost:8000/ws";
const MIC_WS_URL = "ws://localhost:8000/ws/mic";
const API_URL    = "http://localhost:8000";

// ── DOM refs ─────────────────────────────────────────────────
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

// ── PDF state ─────────────────────────────────────────────────
let pdfContext  = "";
let pdfFilename = "";

// ── Smart routing keywords ─────────────────────────────────────
// If question contains these words, always go external even if PDF loaded
const EXTERNAL_KEYWORDS = [
  "search", "google", "news", "latest", "current", "today",
  "weather", "price", "stock", "who is", "what is happening",
  "hubspot", "crm", "contact", "deal", "slack", "github"
];

function shouldUsePdf(question) {
  if (!pdfContext) return false;
  const q = question.toLowerCase();
  // Force external if question clearly isn't about the document
  if (EXTERNAL_KEYWORDS.some(kw => q.includes(kw))) return false;
  return true;
}

// ── WebSocket ─────────────────────────────────────────────────
let ws;
function connectWS() {
  ws = new WebSocket(WS_URL);
  ws.onopen    = () => setConnState("ok");
  ws.onmessage = (evt) => { removeTyping(); renderBotResponse(JSON.parse(evt.data)); };
  ws.onclose   = () => { setConnState("err"); setTimeout(connectWS, 2500); };
  ws.onerror   = () => setConnState("err");
}
connectWS();

function setConnState(s) {
  connBadge.textContent = s === "ok" ? "● Connected" : "● Disconnected";
  connBadge.className   = "conn-badge " + (s === "ok" ? "ok" : "err");
  wsDot.className       = "status-dot " + (s === "ok" ? "connected" : "error");
}

// ── Send message ──────────────────────────────────────────────
function sendMessage() {
  const text = msgInput.value.trim();
  if (!text) return;
  msgInput.value = "";

  if (shouldUsePdf(text)) {
    sendPdfQuestion(text);
  } else {
    // Normal agent pipeline (WebSocket)
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
  addUserMessage(question, [{ cls: "pdf", label: "PDF" }]);
  showTyping();

  try {
    const res = await fetch(`${API_URL}/ask-pdf`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        question,
        pdf_text: pdfContext.slice(0, 12000)
      }),
    });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Server ${res.status}: ${err}`);
    }

    const data = await res.json();
    removeTyping();

    // ── Not in PDF → hand off to the normal agent pipeline ────
    if (data.redirect) {
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        addBotMessage("⚠ Not connected to agent pipeline. Please wait…");
        return;
      }
      showTyping();
      ws.send(question);   // WebSocket triggers research / other agents
      return;
    }

    renderPdfAnswer(data.answer || data.chat || "(no response)");

  } catch (err) {
    removeTyping();
    console.error("PDF Q&A error:", err);
    addBotMessage(`⚠ PDF Q&A failed: ${err.message}`);
  }
}

// ── Render PDF answer with page badges ───────────────────────
function renderPdfAnswer(text) {
  // Extract "Sources: Page 2, Page 4" from end of answer
  const srcMatch = text.match(/Sources\s*:\s*([^\n]+)$/im);
  let mainText = text;
  let pages    = [];

  if (srcMatch) {
    mainText = text.slice(0, srcMatch.index).trim();
    pages = srcMatch[1]
      .split(",")
      .map(s => s.trim().replace(/^page\s*/i, "Page "))
      .filter(Boolean);
  }

  const el = document.createElement("div");
  el.className = "msg bot";
  el.innerHTML = `
    <div class="msg-bubble">${formatResponse(mainText)}</div>
    ${pages.length ? `
      <div class="page-sources">
        <span class="sources-label">Sources</span>
        ${pages.map(p => `<span class="page-badge">📄 ${p}</span>`).join("")}
      </div>` : ""}
    <div class="msg-meta">
      <span class="meta-tag pdf">PDF Answer</span>
    </div>`;
  chat.appendChild(el);
  scrollBottom();
}

// ── Generic render helpers ────────────────────────────────────
function addUserMessage(text, tags = []) {
  const el = document.createElement("div");
  el.className = "msg user";
  el.innerHTML = `
    <div class="msg-bubble">${escHtml(text)}</div>
    <div class="msg-meta">
      
    </div>`;
  chat.appendChild(el); scrollBottom();
}

function addBotMessage(text, tags = []) {
  const el = document.createElement("div");
  el.className = "msg bot";
  el.innerHTML = `
    <div class="msg-bubble">${formatResponse(text)}</div>
    <div class="msg-meta">
      ${tags.map(t => `<span class="meta-tag ${t.cls}">${t.label}</span>`).join("")}
    </div>`;
  chat.appendChild(el); scrollBottom();
}

function renderBotResponse(data) {
  const tags = [];
  if (data.mcp)               tags.push({ cls: "mcp",  label: "MCP" });
  if (data.results?.code)     tags.push({ cls: "code", label: "Code" });
  if (data.results?.research) tags.push({ cls: "",     label: "Research" });
  updatePills(data.results || {});
  addBotMessage(data.chat || data.answer || "(no response)", tags);
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
function removeTyping()  { document.getElementById("typingIndicator")?.remove(); }
function scrollBottom()  { chat.scrollTop = chat.scrollHeight; }
function timestamp()     { return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); }
function escHtml(s) {
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;")
                  .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
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

  addUserMessage(`📄 ${file.name}`, [{ cls: "pdf", label: "PDF" }]);
  showTyping();

  const formData = new FormData();
  formData.append("file", file);
  formData.append("question", "");

  try {
    const res = await fetch(`${API_URL}/upload-pdf`, { method: "POST", body: formData });

    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Server ${res.status}: ${err}`);
    }

    const data = await res.json();
    removeTyping();

    // Store extracted text for follow-up Q&A
    pdfContext  = data.pdf_text || "";
    pdfFilename = file.name;

    showPdfBanner(file.name, data.page_count, data.truncated);
    addBotMessage(
      `✅ **${file.name}** indexed — ${data.page_count} page(s) ready.\nAsk me anything about this document.`,
      [{ cls: "pdf", label: "PDF Indexed" }]
    );

  } catch (err) {
    removeTyping();
    console.error("PDF upload error:", err);
    addBotMessage(`⚠ PDF upload failed: ${err.message}`);
  }
});

function showPdfBanner(name, pages, truncated) {
  pdfBannerTxt.textContent =
    `${name} · ${pages} page(s) indexed${truncated ? " · truncated" : ""} · Questions about doc go to PDF · Others go to agents`;
  pdfBanner.style.display = "flex";
  msgInput.placeholder    = `Ask about ${name}, or ask anything else…`;
}

function clearPdf() {
  pdfContext  = "";
  pdfFilename = "";
  pdfBanner.style.display = "none";
  msgInput.placeholder    = "Message the agents…";
}

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
    analyser  = audioCtx.createAnalyser(); analyser.fftSize = 256;
    src.connect(analyser); drawWave();

    micWs = new WebSocket(MIC_WS_URL);
    micWs.binaryType = "arraybuffer";
    micWs.onmessage  = (evt) => {
      const data = JSON.parse(evt.data); removeTyping();
      if (data.type === "transcript") {
        addUserMessage(data.text, [{ cls: "mic", label: "Transcribed" }]);
        showTyping();
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
      micTimer.textContent =
        `${Math.floor(timerSec/60)}:${String(timerSec%60).padStart(2,"0")}`;
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
    ctx.lineTo(W, H/2); ctx.stroke();
  }
  render();
}

// ── Audio / Video upload ──────────────────────────────────────
document.getElementById("audioFile").addEventListener("change", async function () {
  const file = this.files[0]; if (!file) return; this.value = "";
  addUserMessage(`🎵 ${file.name}`, [{ cls: "", label: "Audio" }]); showTyping();
  const fd = new FormData(); fd.append("file", file);
  try {
    const data = await (await fetch(`${API_URL}/upload-audio`, { method:"POST", body:fd })).json();
    removeTyping();
    addUserMessage(data.transcript, [{ cls: "mic", label: "Transcribed" }]);
    renderBotResponse(data);
  } catch (err) { removeTyping(); addBotMessage("⚠ Audio failed: " + err.message); }
});

document.getElementById("videoFile").addEventListener("change", async function () {
  const file = this.files[0]; if (!file) return; this.value = "";
  addUserMessage(`🎬 ${file.name}`, [{ cls: "", label: "Video" }]); showTyping();
  const fd = new FormData(); fd.append("file", file);
  try {
    const data = await (await fetch(`${API_URL}/upload-video`, { method:"POST", body:fd })).json();
    removeTyping();
    addUserMessage(data.transcript, [{ cls: "mic", label: "Transcribed" }]);
    renderBotResponse(data);
  } catch (err) { removeTyping(); addBotMessage("⚠ Video failed: " + err.message); }
});

// ── MCP Panel ─────────────────────────────────────────────────
function toggleMcpPanel() { if (mcpPanel.classList.toggle("open")) loadMcpTools(); }

async function loadMcpTools() {
  mcpTools.innerHTML = "Loading…";
  try {
    const data  = await (await fetch(`${API_URL.replace("8000","8001")}/mcp/tools`)).json();
    const tools = data.tools || {};
    mcpTools.innerHTML = Object.keys(tools).length
      ? Object.entries(tools).map(([n,i]) => `
          <div class="mcp-tool-card">
            <div class="mcp-tool-name">${n}</div>
            <div class="mcp-tool-desc">${i.description}</div>
            <div class="mcp-provider">${i.provider}</div>
          </div>`).join("")
      : `<span style="color:var(--muted);font-size:12px">No tools registered</span>`;
  } catch {
    mcpTools.innerHTML = `<span style="color:var(--red);font-size:12px">MCP server unreachable</span>`;
  }
}
