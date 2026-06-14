# 🏦 Enterprise Multi-Agent Banking Mesh

![Deploy to Test](https://github.com/Eran-Meir/multi-agent-banking-mesh/actions/workflows/1-deploy-to-test.yml/badge.svg)
![Release to Prod](https://github.com/Eran-Meir/multi-agent-banking-mesh/actions/workflows/3-release-to-prod.yml/badge.svg)

This repository contains an enterprise-grade, cloud-native **Multi-Agent Banking System** designed for high-security deployment on Google Kubernetes Engine (GKE) Autopilot. 

Rather than a monolithic AI script, this system implements a highly decoupled **Microservice AI Topology**. It is designed specifically for financial institutions, featuring extreme scalability, isolated personality modules, and strict compliance guardrails.

---

## 🏗️ The Multi-Agent Microservice Topology

The system uses a highly scalable "Traffic Cop" routing pattern to ensure AI requests are handled efficiently and independently.

1. **The Orchestrator Agent (API Gateway):** The user never interacts directly with specialized agents. Every request hits the Orchestrator. It acts as the routing intelligence, identifying the user's intent and proxying the request to the appropriate downstream agent. It can also synthesize answers from multiple agents for complex queries.
2. **The Profiler Agent:** Analyzes and stores user context, spending behaviors, and investment risk tolerance.
3. **The Expense Analyst Agent:** Securely crunches heavy datasets (e.g., thousands of bank transactions) via asynchronous GCP Pub/Sub queues to detect spending anomalies.
4. **The Wealth Advisor Agent:** Consumes data from the Profiler and Expense Analyst to generate personalized, risk-adjusted investment insights.

> **💡 Why Microservices?** Each agent is a separate Kubernetes `Deployment` with its own `HorizontalPodAutoscaler` (HPA). If 10,000 users suddenly ask for stock advice, the Wealth Advisor scales from 1 to 50 pods instantly, while the Expense Analyst stays at 1 pod. They scale completely independently based on real-time traffic.

---

## 🛡️ The 5 Pillars of Enterprise AI Architecture

To meet strict banking compliance and cost-control requirements, this architecture implements five critical enterprise guardrails:

### 1. Security & PII Redaction (Model Armor)
Raw customer data (SSNs, Account Numbers) must never reach public LLM APIs.
* **GCP Cloud DLP:** Automatically scrubs and redacts PII before processing.
* **Google Cloud Model Armor:** Actively intercepts malicious prompt-injection attacks (jailbreaks), filters toxic content, and enforces strict corporate safety policies.

### 2. Semantic Caching (Latency & Cost Control)
If 1,000 users ask *"What are the current federal interest rates?"*, we do not query the LLM 1,000 times.
* A **Semantic Cache** (e.g., Redis or Vertex AI Feature Store) intercepts the prompt, evaluates the "meaning" of the question via embeddings, and returns a cached answer if a similar question was recently asked. This drops LLM costs by 40% and reduces latency to <50ms.

### 3. LLM-Ops & Hallucination Tracking
Standard CPU/RAM monitoring is insufficient for AI. 
* We implement **LLM-Ops** (via LangSmith or Vertex AI Model Evaluation) to trace the exact prompt, measure token usage per request, track LLM generation latency, and log user feedback directly to BigQuery for continuous prompt fine-tuning.

### 4. Grounding via RAG (Retrieval-Augmented Generation)
The Wealth Advisor does not guess the bank's internal mortgage rates. 
* It uses a **Vector Database** (e.g., Vertex AI Vector Search or pgvector) to retrieve proprietary bank policy documents and inject them into the LLM context window. The AI only provides answers grounded in strictly vetted corporate data.

### 5. Zero-Trust Network Security
* The GKE Autopilot cluster is entirely private. 
* We use **VPC Service Controls (VPC-SC)** to draw a secure perimeter around the GCP project. Even with compromised service account keys, data cannot be exfiltrated outside the corporate network.

---

## 💥 The Zero-Billing Killswitch

To ensure strict cost control during development, this repository implements a fully automated **Billing Killswitch**. 

A GCP Budget is wired to a Pub/Sub topic. If infrastructure costs exceed the **$9.00 USD** threshold, an event-driven Gen 2 Cloud Function automatically intercepts the billing alert and fires a payload to GitHub Actions. This immediately triggers the `6. Nuke Everything` pipeline, aggressively destroying all Terraform infrastructure and terminating the project to guarantee a strict $0/month baseline.

---

## 🗺️ Environment Architectures

### Test Environment (Cost-Optimized & Scalable)
The Test environment is isolated to a single region with a strictly capped Horizontal Pod Autoscaler (HPA) to prove the scaling mechanics without incurring massive costs.

```mermaid
graph TD
    User((User)) ==> |HTTP Request| RLB[Regional Load Balancer]
    Artifacts[Google Artifact Registry] -.-> |Pulls Image| Orch
    RLB ==> Orch[Orchestrator API Gateway<br/>Base: 1 Pod]

    subgraph Test [Test Environment: me-west1]
        direction TB
        Orch -.- |HPA Autoscales to 2| OrchR[+1 Replica]
        
        Orch ==> |Publishes Event| Topic{GCP Pub/Sub Topic}
        
        Topic -.-> |Async Subscribe| Analyst[Expense Analyst<br/>Base: 1 Pod]
        Analyst -.- |HPA Autoscales to 2| AnalystR[+1 Replica]
        
        Topic -.-> |Async Subscribe| Wealth[Wealth Advisor<br/>Base: 1 Pod]
        Wealth -.- |HPA Autoscales to 2| WealthR[+1 Replica]
    end
```

### Production Environment (High-Availability Active-Active)
The Production environment operates in a fully Active-Active multi-region topology. It handles significantly higher traffic bounds and ensures total failover reliability.

```mermaid
graph TD
    User((Global User)) ==> |HTTP| GLB[Global Load Balancer]
    Artifacts[Google Artifact Registry] -.-> |Pulls Image| OrchP
    Artifacts -.-> |Pulls Image| OrchS

    GLB ==> |Primary Route| RLB_P[Regional Load Balancer]
    GLB -.-> |Failover Route| RLB_S[Regional Load Balancer]

    subgraph Primary [Primary Region: europe-west4]
        RLB_P ==> OrchP[Orchestrator<br/>Base: 1 Pod]
        OrchP -.- |HPA Autoscales to 4| OrchP_R[+3 Replicas]
        OrchP ==> TopicP{Pub/Sub Topic}
        TopicP -.-> AnalystP[Expense Analyst<br/>Base: 1 Pod]
        AnalystP -.- |HPA Autoscales to 4| AnalystP_R[+3 Replicas]
    end

    subgraph Secondary [Secondary Region: europe-west3]
        RLB_S ==> OrchS[Orchestrator<br/>Base: 1 Pod]
        OrchS -.- |HPA Autoscales to 4| OrchS_R[+3 Replicas]
        OrchS ==> TopicS{Pub/Sub Topic}
        TopicS -.-> AnalystS[Expense Analyst<br/>Base: 1 Pod]
        AnalystS -.- |HPA Autoscales to 4| AnalystS_R[+3 Replicas]
    end
```
