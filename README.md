# 🛡️ NovaShield

> **Intelligent, scalable threat detection for the modern web.**

Welcome to **NovaShield**, a highly responsive, distributed cybersecurity system designed to autonomously detect malicious and phishing websites. By combining a distributed crawling architecture with robust Machine Learning classification, NovaShield evaluates URLs in real time to keep users safe from evolving web threats.

---

### 🧠 Intelligence Core
NovaShield is trained on the **[UCI Phishing Websites Dataset](https://archive.ics.uci.edu/ml/datasets/Phishing+Websites)**, a gold-standard academic repository containing over **11,000 expert-verified samples**. This ensures our AI brain is built on rigorous, real-world cybersecurity evidence.

---

## 🏗️ Project Architecture

NovaShield is built as a suite of modular microservices:

*   **`coordinator/`**: A FastAPI REST API that manages the job queue and dispatches tasks.
*   **`worker/`**: Distributed Celery workers that execute asynchronous web crawls using `aiohttp`.
*   **`ml/`**: The Machine Learning pipeline, featuring feature extraction and ensemble classification.
*   **`dashboard/`**: A sleek, Cyberpunk-themed React + Vite frontend for real-time monitoring.
*   **`data/`**: Local SQLite databases for persistence of job states and scan history.

---

## 🔄 System Flow & Pipeline

NovaShield follows a multi-stage pipeline to transform a raw URL into a comprehensive security verdict.

### 1. The Detection Pipeline
Every URL submitted to the system passes through four specialized intelligence layers:

1.  **Safety & Crawling Layer**: The `Worker` performs a safe, asynchronous fetch of the website content, enforcing **SSRF Protection** to block scans of internal networks.
2.  **Structural Extraction Layer**: The `FeatureExtractor` maps the URL and HTML into a 17-dimension vector based on the UCI standard (SSL status, TLD risk, anchor ratios, etc.).
3.  **Linguistic Analysis Layer**: The `NLP Analyzer` scans body text and scripts for high-risk phishing keywords and patterns.
4.  **Inference & Heuristics Layer**: 
    *   **ML Ensemble**: A combination of Random Forest, Gradient Boosting, and Logistic Regression calculates the base probability.
    *   **Risk Rules**: A final "Expert System" layer applies penalties for brand impersonation and suspicious lexical patterns.

### 2. Data Flow Diagram

```mermaid
graph TD
    A[User/Dashboard] -->|POST /api/scan| B(Coordinator API)
    B -->|Create Job| C[(SQLite DB)]
    B -->|Dispatch Task| D{Redis Broker}
    D -->|Consume| E[Celery Worker]
    E -->|1. Safe Fetch| F[Web Crawler]
    E -->|2. Feature Extraction| G[ML Model]
    E -->|3. Risk Heuristics| H[Expert Rules]
    G & H -->|Update Status| C
    C -->|Real-time Poll| A
```

---

---

## 🚀 Getting Started

NovaShield supports two primary execution modes: **Direct Mode** for local development and **Distributed Mode** for scalable deployments.

### 📋 Prerequisites

*   **Python 3.10+**
*   **Node.js 18+**
*   **Docker & Docker Compose** (Required for Distributed Mode)

---

### 🛠️ Mode 1: Direct Mode (Local Development)
Ideal for quick testing and single URL scans.

#### 1. Terminal 1: Backend API
```bash
python -m uvicorn coordinator.api:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Terminal 2: Frontend Dashboard
```bash
cd dashboard
npm run dev
```

---

### 🚀 Mode 2: Distributed Mode (High-Performance)
Use this mode to handle large volumes of URLs across multiple worker nodes.

#### 1. Start the Message Broker (Redis)
Ensure you have Redis running (either natively or via a simple Docker container):
```bash
docker run -d -p 6379:6379 --name ns-redis redis:7-alpine
```

#### 2. Start the Celery Worker(s)
Open one or more terminals and run the following to create your worker cluster:
```bash
python -m celery -A worker.worker_main.celery_app worker --pool=solo --loglevel=info
```
*   **To Scale**: Simply open more terminals and run the same command. Each new terminal adds more "muscle" to the system.

#### 3. Management
*   **Clear Queue**: Handled automatically on restart.
*   **Stop System**: Press `Ctrl+C` in each terminal and run `docker stop ns-redis`.

## 🔒 Service Reference

| Service | Mode | URL |
| :--- | :--- | :--- |
| **Dashboard** | Both | [http://localhost:5173](http://localhost:5173) |
| **API Backend** | Both | [http://localhost:8000](http://localhost:8000) |
| **API Docs (Swagger)**| Both | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **Redis Broker** | Docker | `localhost:6379` |

---

## 🧪 Quick Test
Once the system is running, you can verify the new **Heuristic Risk Rules** by scanning a high-risk URL like:
`http://paypa1-secure-verify.xyz/login/account/secure/index.exe`

---

Developed with ❤️ for a safer web.
