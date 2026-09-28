# 🤖 Intellexa - AI Content Analysis Assistant

<p align="center">
  <em>Chat with YouTube videos, research papers, news articles, and web content like never before!</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue.svg" alt="Python Version">
  <img src="https://img.shields.io/badge/Streamlit-UI Framework-red.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/LangChain-AI Orchestration-orange.svg" alt="LangChain">
  <img src="https://img.shields.io/badge/RAG-Enhanced-green.svg" alt="RAG Enhanced">
</p>

## 🎯 What is Intellexa?

Intellexa is an advanced AI assistant that lets you have meaningful conversations with various content types. Simply provide a YouTube URL or web content link, and instantly chat with the content using our enhanced RAG pipeline with LangGraph memory.

### 🌟 Why Choose Intellexa?

| Feature | Advantage |
|---------|-----------|
| **🎥 YouTube Video Analysis** | Extract transcripts and chat with any YouTube video content, with timestamp references |
| **📚 Multi-Format Support** | Process PDFs, ArXiv papers, news articles, blogs, and webpages |
| **🧠 Smart Content Routing** | Three-tier routing that answers simple queries without extra LLM calls |
| **🌍 Multilingual** | Chat in English, Hindi, French, Spanish, and German |
| **🎵 Voice Interaction** | Speak your queries and get audio responses |
| **💬 Context-Aware Memory** | Remembers conversation history across interactions |
| **⚡ Fast Inference** | Quick responses powered by Groq's high-speed LLMs |

## 🏗 System Architecture

![System Architecture](Intellexa%20architecture.png)

Intellexa is organised into five layers:

| Layer | Role |
|-------|------|
| **Presentation** | Streamlit UI for content loading, text and voice queries, and audio playback |
| **Orchestrator** | LangGraph workflow that routes each query and generates the response |
| **Ingestion** | Format-specific processors for web, PDF, ArXiv, news, and YouTube, run only when a URL is loaded |
| **Data** | ChromaDB vector store with a separate collection for each source |
| **External Services** | Groq API (LLM), Edge TTS (audio), and youtube-transcript-api (transcripts) |

### Query Routing
1. **Tier 1** → Regex patterns answer greetings and casual queries instantly
2. **Tier 2** → Keyword checks detect video- or document-related questions
3. **Tier 3** → An LLM router classifies anything still ambiguous

Retrieved chunks are selected with **MMR (λ = 0.3)** so answers draw from varied parts of the content rather than near-identical passages.

## 📊 Performance

| Test | Result |
|------|--------|
| **Web query response time** | 2.87 s average |
| **PDF query response time** | 6.87 s average |
| **Content loading** | 100% success across 20 web and PDF sources |
| **MMR vs. standard retrieval** | +1.51% diversity across 80 query comparisons |

*Measured on a local machine (Intel Core i7, 16 GB RAM) using the Groq free tier.*

## 🚀 Quick Start

### Prerequisites: Python 3.11 & [Groq API Key](https://console.groq.com/keys)

```bash
# 1. Clone and setup
git clone https://github.com/sapana27/Intellexa-Content_Analysis_AI.git
cd Intellexa-Content_Analysis_AI

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment: create a .env file containing
#    GROQ_API_KEY=your_groq_api_key_here

# 5. Launch application
streamlit run frontend.py
```

The application will open at `http://localhost:8501`

<!-- ## 📹 Demo Video

![Demo Video](demo_video.mp4)

*Watch Intellexa in action: Processing YouTube videos, analyzing research papers, and providing intelligent responses with audio support.* -->

## 🛠 Usage Guide

### 1. Load Content
- **YouTube**: Paste URL in sidebar → Select language → Click "Load YouTube Video"
- **Web Content**: Paste PDF/article URL → Click "Load Web Content"

### 2. Ask Questions
- **Type** in chat input or **click microphone** for voice
- Ask about content, summaries, specific sections, or general queries

### 3. Get Responses
- Read AI responses with context from your content
- Toggle audio playback in sidebar for voice responses

## 🔧 Technical Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Streamlit |
| **AI Framework** | LangChain, LangGraph |
| **LLM** | Groq (Llama-3.3-70b) |
| **Embeddings** | HuggingFace paraphrase-multilingual-mpnet-base-v2 |
| **Vector Store** | ChromaDB (MMR retrieval) |
| **Content Processing** | YouTube Transcript API, trafilatura, BeautifulSoup, PyPDF2, arxiv, Newspaper3k |
| **Audio** | Edge TTS, Streamlit Mic Recorder |

> **Note:** Groq has retired Llama-3.3-70b-versatile. To use a newer model, update `model_name` in `backend.py`.

## 🤝 Contributing

We welcome contributions! Please feel free to submit pull requests, report bugs, or suggest new features.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

<p align="center">
  <strong>Ready to transform how you interact with content? Start chatting with Intellexa today! 🚀</strong>
</p>