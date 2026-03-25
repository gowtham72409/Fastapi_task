# Multi-Agent AI Workflow System

A FastAPI-based system where multiple AI agents collaborate autonomously to solve complex tasks. The system supports real-time interactions via WebSockets, file uploads for audio/video processing, and persistent memory storage in PostgreSQL.  

## Features

- **Planner Agent**: Determines which agents are needed for each task.
- **Research Agent**: Performs research and summarizes information.
- **Code Agent**: Generates Python code based on task instructions.
- **Audio Agent**: Transcribes uploaded audio or extracted audio from videos.
- **Video Agent**: Extracts audio from video files and converts it to text.
- **Evaluation Agent**: Evaluates the quality of outputs from other agents.
- **Chat Agent**: Provides a conversational response to tasks.
- **Memory Storage**: Saves task history, results, and evaluations in PostgreSQL.
- **Real-Time Communication**: WebSocket endpoint for instant interaction.
- **File Uploads**: Support for audio (`.wav`) and video (`.mp4`) uploads.

---

## Tech Stack

- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: [PostgreSQL](https://www.postgresql.org/)
- **Redis**: For Pub/Sub messaging between agents
- **Audio Processing**: [Faster Whisper](https://github.com/guillaumekln/faster-whisper)
- **Video Processing**: [FFmpeg](https://ffmpeg.org/)
- **AI Core**: [Groq API](https://www.groq.ai/) for LLM-based agent reasoning

---

Create a virtual environment

python -m venv venv
venv\Scripts\activate  

pip install -r requirements.txt

## Multi-Agent System Workflow

```mermaid
flowchart TD
    A[User Input / Task] -->|WebSocket| B[Planner Agent]
    B -->|Decides Agents| C{Agents Needed}
    
    C -->|Research| D[Research Agent]
    C -->|Code| E[Code Agent]
    C -->|Audio| F[Audio Agent]
    C -->|Video| G[Video Agent]
    C -->|Chat| H[Chat Agent]
    
    D --> I[Collect Results]
    E --> I
    F --> I
    G --> I
    H --> I
    
    I --> J[Evaluation Agent]
    J --> K[Chat Agent Response]
    I --> L[Save to PostgreSQL (Memory)]
    
    K -->|Send via WebSocket| M[User Receives Response]
    L -->|Stored Memory| N[Future Tasks Reference]
    
    subgraph File Upload
        O[Audio/Video Upload] --> F
        O --> G
    end