<div align="center">
  <h1>🛡️ ContextShield</h1>
  <p><strong>The Zero-Cost Active Context Optimizer & Token Firewall for AI IDEs.</strong></p>
  
  ![Open Source](https://img.shields.io/badge/Open_Source-Yes-blue.svg)
  ![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
  ![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg?logo=react)
  ![License](https://img.shields.io/badge/License-MIT-green.svg)
</div>

---

## 🌩️ The Problem & Solution
Modern AI IDEs (like Cursor, Antigravity, and Copilot) blindly attach massive amounts of codebase context to LLM providers on every keystroke. This context is notoriously bloated with legacy docstrings, dead code, and huge inline block comments. If you use your own API keys, **you are paying for thousands of useless tokens per request**.

**ContextShield** is a 100% free, local proxy that sits between your IDE and the LLM provider. 
It natively intercepts both standard OpenAI flat messages and deeply nested Google Gemini API structures (`contents`/`parts`). It rips out non-semantic token waste using an Abstract Syntax Tree (AST) parser in-flight, logs your exact financial savings to a local UI, and cleanly forwards the lean payload to a free local LLM (Ollama) or cloud fallbacks (Groq/OpenRouter).

---

## 🏗️ System Architecture
ContextShield uses a completely decoupled, high-performance stack:
- **FastAPI (Python)**: The asynchronous high-speed networking proxy handling SSE streaming.
- **Python `ast` Module**: Native semantic code parsing for completely safe docstring/comment eradication without breaking syntax.
- **React & Vite**: The lightning-fast frontend environment.
- **Recharts**: For dynamic, real-time telemetry rendering.
- **In-Memory Thread-Safe DB**: For lock-safe tracking of highly concurrent request optimization metrics.

---

## 🚀 Setup Guide

### 1. Clone & Install Proxy Dependencies
Navigate into the proxy folder and install the Python backend:
```bash
cd proxy
pip install -r requirements.txt
```
Copy the `.env.example` file to configure your fallback endpoints:
```bash
cp .env.example .env
```
*(Edit `.env` to include your Groq/OpenRouter/Gemini keys if you aren't running a local Ollama instance)*

### 2. Install Frontend Dependencies
Open a new terminal, navigate into the dashboard folder, and install the Vite app:
```bash
cd dashboard
npm install
```

### 3. Start the Environment
To launch both the FastAPI Proxy and the Vite Dashboard simultaneously (with graceful exit handling), simply run our unified startup script from the root directory:
```bash
python start_contextshield.py
```

---

## 🔌 IDE Configuration (The Hijack)
Some modern IDEs stubbornly ignore base URL overrides in their settings panels. To force your IDE to route all internal Chromium/Node network traffic through the ContextShield interceptor, launch the IDE via your terminal using forced proxy environment variables.

**For Antigravity (Windows PowerShell):**
```powershell
$env:HTTP_PROXY="http://127.0.0.1:8000"; $env:HTTPS_PROXY="http://127.0.0.1:8000"; $env:NODE_TLS_REJECT_UNAUTHORIZED="0"; antigravity .
```
*(This traps the entire application's network layer, giving the payload physically nowhere else to go but straight into your proxy interceptor).*

---

## 🔮 Future Scope
- **Electron App Wrapper**: Packaging the FastAPI backend and React frontend into a single, downloadable one-click desktop app with system tray controls.
- **ChromaDB Semantic Caching**: Implementing local vector database caching so duplicate queries are answered instantly without ever hitting an external LLM provider.

---
📝 **License:** MIT
