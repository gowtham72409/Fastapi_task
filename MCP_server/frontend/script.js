/* ── NeuralDesk — script.js ─────────────────────────────────── */

const WS_URL     = "ws://localhost:8000/ws";
const MIC_WS_URL = "ws://localhost:8000/ws/mic";
const API_URL    = "http://localhost:8000";

// ── DOM refs ─────────────────────────────────────────────────
const chat       = document.getElementById("chat");
const msgInput   = document.getElementById("msgInput");
const connBadge  = document.getElementById("connBadge");
const wsDot      = document.getElementById("wsStatus");
const waveBar    = document.getElementById("waveformBar");
const micBtn     = document.getElementById("micBtn");
const waveCanvas = document.getElementById("waveCanvas");
const micTimer   = document.getElementById("micTimer");
const mcpPanel   = document.getElementById("mcpPanel");
const mcpTools   = document.getElementById("mcpTools");
const activePills= document.getElementById("activePills");

// ── Text WebSocket ────────────────────────────────────────────
let ws;

function connectWS() {
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    setConnState("ok");
    console.log("WS connected");
  };

  ws.onmessage = (evt) => {
    removeTyping();
    const data = JSON.parse(evt.data);
    renderBotResponse(data);
  };

  ws.onclose = () => {
    setConnState("err");
    setTimeout(connectWS, 2500);
  };

  ws.onerror = () => setConnState("err");
}

connectWS();

function setConnState(state) {
  if (state === "ok") {
    connBadge.textContent = "● Connected";
    connBadge.className = "conn-badge ok";
    wsDot.className = "status-dot connected";
  } else {
    connBadge.textContent = "● Disconnected";
    connBadge.className = "conn-badge err";
    wsDot.className = "status-dot error";
  }
}

// ── Send text message ─────────────────────────────────────────
function sendMessage() {
  const text = msgInput.value.trim();
  if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;

  addUserMessage(text);
  showTyping();
  ws.send(text);
  msgInput.value = "";
}

msgInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

// ── Render helpers ────────────────────────────────────────────
function addUserMessage(text, tags = []) {
  const el = document.createElement("div");
  el.className = "msg user";
  el.innerHTML = `
    <div class="msg-bubble">${escHtml(text)}</div>
    <div class="msg-meta">
      <span>${timestamp()}</span>
      ${tags.map(t => `<span class="meta-tag ${t.cls}">${t.label}</span>`).join("")}
    </div>`;
  chat.appendChild(el);
  scrollBottom();
}

function addBotMessage(text, tags = []) {
  const el = document.createElement("div");
  el.className = "msg bot";

  el.innerHTML = `
    <div class="msg-bubble">${formatResponse(text)}</div>
    <div class="msg-meta">
      <span>${timestamp()}</span>
      ${tags.map(t => `<span class="meta-tag ${t.cls}">${t.label}</span>`).join("")}
    </div>`;
  chat.appendChild(el);
  scrollBottom();
}

function renderBotResponse(data) {
  const tags = [];
  if (data.mcp)               tags.push({ cls: "mcp",  label: "MCP" });
  if (data.results?.code)     tags.push({ cls: "code", label: "Code" });
  if (data.results?.research) tags.push({ cls: "",     label: "Research" });

  // Show active agent pills in topbar
  updatePills(data.results || {});

  addBotMessage(data.chat || "(no response)", tags);
}

function updatePills(results) {
  const agents = Object.keys(results);
  activePills.innerHTML = agents.map(a =>
    `<span class="pill active">${a}</span>`
  ).join("");
}

function showTyping() {
  const el = document.createElement("div");
  el.className = "msg bot typing-indicator";
  el.id = "typingIndicator";
  el.innerHTML = `<div class="msg-bubble"><div class="dots"><span/><span/><span/></div></div>`;
  chat.appendChild(el);
  scrollBottom();
}

function removeTyping() {
  document.getElementById("typingIndicator")?.remove();
}

function scrollBottom() {
  chat.scrollTop = chat.scrollHeight;
}

function timestamp() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function escHtml(s) {
  return String(s)
    .replace(/&/g,"&amp;")
    .replace(/</g,"&lt;")
    .replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}

function formatResponse(text) {
  // Simple markdown-ish: code blocks
  return escHtml(text)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br>");
}

// ── Mic — live recording ──────────────────────────────────────
let mediaRecorder = null;
let micWs         = null;
let audioChunks   = [];
let timerInterval = null;
let timerSec      = 0;
let analyser      = null;
let animFrame     = null;
let audioCtx      = null;

async function toggleMic() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    stopMic();
  } else {
    await startMic();
  }
}

async function startMic() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    // Waveform analyser
    audioCtx  = new AudioContext();
    const src = audioCtx.createMediaStreamSource(stream);
    analyser  = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    src.connect(analyser);
    drawWave();

    // Open mic WebSocket
    micWs = new WebSocket(MIC_WS_URL);
    micWs.binaryType = "arraybuffer";

    micWs.onopen = () => console.log("Mic WS open");

    micWs.onmessage = (evt) => {
      const data = JSON.parse(evt.data);
      removeTyping();
      if (data.type === "transcript") {
        console.log("Transcript:", data.text);
        addUserMessage(data.text, [{ cls: "mic", label: "Transcribed" }]);
        showTyping(); // waiting for agent result now
      } else if (data.type === "agent_result") {
        renderBotResponse(data);
      }
    };

    micWs.onerror = (e) => console.error("Mic WS error", e);

    // MediaRecorder
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      // Build final blob and send over WS
      const blob = new Blob(audioChunks, { type: "audio/webm" });
      audioChunks = [];

      if (micWs && micWs.readyState === WebSocket.OPEN) {
        const buf = await blob.arrayBuffer();
        showTyping();
        micWs.send(buf);
      }

      stream.getTracks().forEach(t => t.stop());
    };

    mediaRecorder.start();

    // UI state
    micBtn.classList.add("active");
    waveBar.classList.add("active");
    timerSec = 0;
    micTimer.textContent = "0:00";
    timerInterval = setInterval(() => {
      timerSec++;
      const m = Math.floor(timerSec / 60);
      const s = String(timerSec % 60).padStart(2, "0");
      micTimer.textContent = `${m}:${s}`;
    }, 1000);

  } catch (err) {
    alert("Microphone access denied or unavailable:\n" + err.message);
  }
}

function stopMic() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
  clearInterval(timerInterval);
  cancelAnimationFrame(animFrame);
  if (audioCtx) { audioCtx.close(); audioCtx = null; }

  micBtn.classList.remove("active");
  waveBar.classList.remove("active");

  // Close mic WS after short delay (let onstop send the blob first)
  setTimeout(() => {
    if (micWs) { micWs.close(); micWs = null; }
  }, 1500);
}

function drawWave() {
  const ctx  = waveCanvas.getContext("2d");
  const buf  = new Uint8Array(analyser.frequencyBinCount);
  const W    = waveCanvas.width;
  const H    = waveCanvas.height;

  function render() {
    animFrame = requestAnimationFrame(render);
    analyser.getByteTimeDomainData(buf);

    ctx.clearRect(0, 0, W, H);
    ctx.strokeStyle = "#f5495b";
    ctx.lineWidth   = 2;
    ctx.beginPath();

    const sliceW = W / buf.length;
    let x = 0;

    for (let i = 0; i < buf.length; i++) {
      const v = buf[i] / 128;
      const y = (v * H) / 2;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      x += sliceW;
    }

    ctx.lineTo(W, H / 2);
    ctx.stroke();
  }

  render();
}

// ── File upload — audio ───────────────────────────────────────
document.getElementById("audioFile").addEventListener("change", async function () {
  const file = this.files[0];
  if (!file) return;
  this.value = "";   // reset so same file can be re-selected

  addUserMessage(`🎵 Uploading audio: ${file.name}`, [{ cls: "", label: "Audio" }]);
  showTyping();

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res  = await fetch(`${API_URL}/upload-audio`, { method: "POST", body: formData });
    const data = await res.json();
    removeTyping();
    addUserMessage(data.transcript, [{ cls: "mic", label: "Transcribed" }]);
    renderBotResponse(data);
  } catch (err) {
    removeTyping();
    addBotMessage("⚠ Audio upload failed: " + err.message);
  }
});

// ── File upload — video ───────────────────────────────────────
document.getElementById("videoFile").addEventListener("change", async function () {
  const file = this.files[0];
  if (!file) return;
  this.value = "";   // reset input

  addUserMessage(`🎬 Uploading video: ${file.name}`, [{ cls: "", label: "Video" }]);
  showTyping();

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res  = await fetch(`${API_URL}/upload-video`, { method: "POST", body: formData });
    const data = await res.json();
    removeTyping();
    addUserMessage(data.transcript, [{ cls: "mic", label: "Transcribed" }]);
    renderBotResponse(data);
  } catch (err) {
    removeTyping();
    addBotMessage("⚠ Video upload failed: " + err.message);
  }
});

// ── MCP Panel ─────────────────────────────────────────────────
function toggleMcpPanel() {
  const open = mcpPanel.classList.toggle("open");
  if (open) loadMcpTools();
}

async function loadMcpTools() {
  mcpTools.innerHTML = "Loading…";
  try {
    const res   = await fetch(`${API_URL.replace("8000", "8001")}/mcp/tools`);
    const data  = await res.json();
    const tools = data.tools || {};

    if (!Object.keys(tools).length) {
      mcpTools.innerHTML = `<span style="color:var(--muted);font-size:12px">No tools registered</span>`;
      return;
    }

    mcpTools.innerHTML = Object.entries(tools).map(([name, info]) => `
      <div class="mcp-tool-card">
        <div class="mcp-tool-name">${name}</div>
        <div class="mcp-tool-desc">${info.description}</div>
        <div class="mcp-provider">${info.provider}</div>
      </div>
    `).join("");
  } catch {
    mcpTools.innerHTML = `<span style="color:var(--red);font-size:12px">MCP server unreachable</span>`;
  }
}