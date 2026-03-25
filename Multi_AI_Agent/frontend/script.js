const chatBox = document.getElementById("chat");

let ws;

function connectWS() {
    ws = new WebSocket("ws://localhost:8000/ws");

    ws.onopen = () => {
        console.log("Connected");
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        addMessage("bot", data.chat);
    };

    ws.onclose = () => {
        console.log("Disconnected. Reconnecting...");
        setTimeout(connectWS, 2000);
    };
}

connectWS();


function addMessage(type, text) {
    const msg = document.createElement("div");
    msg.classList.add("message", type);
    msg.innerText = text;

    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}


function sendMessage() {
    const input = document.getElementById("message");
    const text = input.value;

    if (!text) return;

    addMessage("user", text);
    ws.send(text);

    input.value = "";
}


function uploadAudio() {
    document.getElementById("audioFile").click();
}

document.getElementById("audioFile").addEventListener("change", async function() {
    const file = this.files[0];
    if (!file) return;

    addMessage("user", "Uploading audio...");

    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("http://localhost:8000/upload-audio", {
        method: "POST",
        body: formData
    });

    const data = await res.json();

    addMessage("bot", "Transcribed: " + data.input);
    addMessage("bot", data.output.chat);
});


function uploadVideo() {
    document.getElementById("videoFile").click();
}

document.getElementById("videoFile").addEventListener("change", async function() {
    const file = this.files[0];
    if (!file) return;

    addMessage("user", "Uploading video...");

    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("http://localhost:8000/upload-video", {
        method: "POST",
        body: formData
    });

    const data = await res.json();

    addMessage("bot", "Transcribed: " + data.input);
    addMessage("bot", data.output.chat);
});

