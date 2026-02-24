# FAUE Technical Documentation

## 🏗️ Building the Intelligence Layer for Fashion

Welcome to FAUE's technical documentation. This directory contains the system architecture, service boundaries, and technical decisions driving our **Global & Cultural Fashion Intelligence Platform**.

---

## 📚 Documentation Structure

```text
docs/
├── README.md                      # You are here
├── 01_SYSTEM_ARCHITECTURE.md      # High-level architecture & data flows
├── 02_THE_ARCHIVE.md              # (WIP) Vectorization, pgvector & image privacy
└── 03_ATELIER_ENGINE.md           # (WIP) GenAI styling logic & VTO orchestration

```

### [01. System Architecture](./01_SYSTEM_ARCHITECTURE.md)

**Start here** to understand how FAUE's microservices interact.

* High-level architecture diagrams
* Core service breakdown (API Gateway, Archive, Atelier)
* Communication patterns (Sync vs. Async)
* Data layer and semantic matching

---

## 🚀 Quick Start for Developers

**Prerequisites:**

* Python 3.11+ (FastAPI)
* PostgreSQL 15+ (with `pgvector` extension)
* Redis 7+ (Caching & Sessions)
* RabbitMQ (Event Bus)
* Docker & Docker Compose

**1. Environment Setup:**

```bash
# Clone the repository
git clone [https://github.com/faueofficial/faue-backend.git](https://github.com/faueofficial/faue-backend.git)
cd faue-backend

# Copy environment variables
cp .env.example .env

```

**2. Start Local Infrastructure:**

```bash
# Start Postgres, Redis, and RabbitMQ
docker-compose up -d db redis rabbitmq

# Verify services are healthy
docker ps

```

**3. Run the Microservices:**

```bash
# In separate terminal windows or using a process manager:
make run-gateway   # Port 8000 (Backend-For-Frontend / Auth / Routing)
make run-archive   # Port 8001 (Wardrobe & Vectorization)
make run-atelier   # Port 8002 (AI Styling Engine & VTO)

```

---

## 🔐 Security & Privacy First

Because we handle personal imagery and body data for Virtual Try-On (VTO), privacy is baked into our architecture:

1. **Ephemeral Data:** VTO images are strictly temporary and auto-deleted within 24 hours via CRON jobs unless explicitly saved.
2. **Private Storage:** All wardrobe images sit behind short-lived, presigned S3/R2 URLs. We do not use public buckets.
3. **Facial Cropping:** Optional automatic neck-down cropping for wardrobe uploads to protect user identity.

---

## 📧 Contact & Support

For architectural queries, access requests, or engineering onboarding:

* **Engineering Team:** engineering@faueofficial.com
* **GitHub Issues:** Please tag `#architecture` for system design discussions.

```
