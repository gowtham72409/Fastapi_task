const ws = new WebSocket("ws://localhost:8000/ws/audio");
const messages = document.getElementById("messages");

function add(text, cls) {
  const div = document.createElement("div");
  div.className = "msg " + cls;
  div.innerText = text;
  messages.appendChild(div);
}

function startRecording() {
  navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
      const recorder = new MediaRecorder(stream); 

      let chunks = [];

      recorder.ondataavailable = e => {
        chunks.push(e.data);
      };

      recorder.onstop = async () => {
        const blob = new Blob(chunks, { type: "audio/webm" });
        const buffer = await blob.arrayBuffer(); // Convert to ArrayBuffer
        console.log("🎤 Sending audio bytes...");
        ws.send(buffer); // Send as binary
    };

      recorder.start();

      setTimeout(() => recorder.stop(), 3000);
    });
}

ws.onmessage = e => {
  const data = JSON.parse(e.data);

  add("You: " + data.text, "user");

  if (data.context && data.context.length > 0) {
  add("Memory: " + data.context.join(", "), "context");
}

  add("AI: " + JSON.stringify(data.result), "bot");
};