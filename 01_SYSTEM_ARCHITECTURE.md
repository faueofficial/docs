# System Architecture

## Overview

FAUE utilizes a lean, domain-driven microservices architecture. Client requests are orchestrated by a centralized Backend-For-Frontend (BFF) API Gateway. The system is designed to handle high-friction visual data (images, vector embeddings) and generative AI workloads (LLM prompting, VTO) asynchronously while keeping the user-facing interactions incredibly fast.

## Core Services

### 1. API Gateway (Port 8000)

The Backend-For-Frontend (BFF). Acts as the single entry point for all direct client interactions, routing traffic to downstream services.

* **Auth & OAuth:** Centralized identity (Magic links, Google, IG, Pinterest).

* **Style DNA Quiz:** Serves visual questions and computes the user's fashion persona.

* **Occasion Routing:** Manages global and cultural event triggers (e.g., Owambe, Corporate).

* **Rate Limiting & Security:** Protects downstream AI and database resources directly via application-level middlewares (e.g., Redis-backed rate limiting).

### 2. Archive (Port 8001)

The user's intelligent digital wardrobe. Replaces the legacy "Vault".

* **Secure Storage:** Manages S3/R2 presigned URLs for privacy-first image hosting.

* **Vectorization:** Runs a lightweight CLIP model to convert clothing images into mathematical embeddings.

* **Social Sync:** Background RabbitMQ workers to ingest and tag Pinterest boards and IG saves.

### 3. Atelier (Port 8002)

The AI Styling and Intelligence Engine.

* **Context Builder:** Injects the user's Style DNA and selected occasion into the prompt.

* **GenAI Stylist:** Queries LLMs to generate structured, highly fashionable outfit schemas in JSON.

* **Semantic Matcher:** Queries the Archive's `pgvector` database to find items the user already owns that match the AI's recommendation.

* **VTO Orchestrator:** Manages the heavy async jobs for Virtual Try-On via external providers (Fashn.ai, Replicate).

## Architecture Diagram

                                      ┌─────────────┐
                                      │    CLIENT   │
                                      │ (Web/Mobile)│
                                      └──────┬──────┘
                                             │ HTTPS / REST
                                             ▼
                                ┌────────────────────────┐
                                │      api-gateway       │
                                │         :8000          │
                                │  (Auth, Rate Limits,   │
                                │   Style DNA, Routing)  │
                                └──────┬──────────┬──────┘
                                       │          │
                      ┌────────────────┘          └────────────────┐
                      ▼                                            ▼
              ┌──────────────┐                             ┌──────────────┐
              │   archive    │                             │   atelier    │
              │    :8001     │                             │    :8002     │
              │              │                             │              │
              │ ┌──────────┐ │                             │ ┌────────────┐
              │ │Upload Svc│ │                             │ │GenAI Stylist│
              │ │(Presigned│ │                             │ │(LLM Chain) │
              │ │ URLs)    │ │                             │ └────────────┘
              │ └──────────┘ │                             │ ┌────────────┐
              │ ┌──────────┐ │                             │ │VTO Layer   │
              │ │Pinterest │ │                             │ │(Ephemeral  │
              │ │Sync Wkr  │ │                             │ │ Image Gen) │
              │ └──────────┘ │                             │ └────────────┘
              │ ┌──────────┐ │                             │ ┌────────────┐
              │ │CLIP model│ │                             │ │pgvector    │
              │ │Vectorizer│ │                             │ │Semantic    │
              │ └──────────┘ │                             │ │Matcher     │
              └───────┬──────┘                             │ └────────────┘
                      │                                    └───────┬──────┘
                      │                                            │
             ┌────────▼────────────┐                     ┌─────────▼───────────┐
             │     PostgreSQL      │                     │    External APIs    │
             │  (w/ pgvector ext)  │                     │  ┌────────────────┐ │
             │                     │                     │  │ Gemini/OpenAI  │ │
             │  schema: gateway    │                     │  └────────────────┘ │
             │  schema: archive    │                     │  ┌────────────────┐ │
             │  schema: atelier    │                     │  │  Fashn.ai VTO  │ │
             └────────┬────────────┘                     │  └────────────────┘ │
                      │                                  │  ┌────────────────┐ │
             ┌────────▼────────────┐                     │  │ Pinterest API  │ │
             │        Redis        │                     │  └────────────────┘ │
             └─────────────────────┘                     └─────────────────────┘
 

## Core Data Flows

### 1. The Vector Matching Flow (Styling)

When a user requests an outfit for an occasion, we want to recommend things they *already own* alongside new items.

1. **Atelier** queries the LLM for an outfit based on the user's *Style DNA*.

2. The LLM returns a structured description: *"Black tailored wool trousers"*.

3. **Atelier** converts this text into a vector embedding.

4. It queries the **Archive's** `pgvector` database using cosine distance.

5. If a match > 85% similarity is found, the system flags the AI recommendation with the user's actual owned item.

### 2. Privacy-First Virtual Try-On (VTO)

VTO requires processing sensitive full-body imagery.

1. Client requests a Try-On via **API Gateway**.

2. **Atelier** creates an async job and immediately returns a `job_id` to the client.

3. The VTO worker sends the images to the provider (e.g., Fashn.ai) with a strictly enforced non-retention flag.

4. The generated image is stored in **Archive** with an `is_ephemeral: true` flag.

5. A background CRON job permanently purges the image from S3/R2 after 24 hours unless the user manually saves it.

## Data Layer Overview

To keep infrastructure simple in V1, we use a single highly-available PostgreSQL instance, isolated by schemas per service.

| Schema | Key Tables | Purpose | 
 | ----- | ----- | ----- | 
| `gateway` | `users`, `style_dna`, `oauth_tokens` | Identity, OAuth, and Viral loop data | 
| `archive` | `wardrobe_items` (contains `vector(512)`) | Digital closet, sources (IG/Pin), Embeddings | 
| `atelier` | `styling_sessions`, `vto_jobs` | Prompt traces, AI outputs, Async job queues | 

*Note: The `pgvector` extension must be enabled on the database for semantic matching to function.*
