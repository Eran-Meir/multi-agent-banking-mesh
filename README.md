# 🏦 Enterprise Multi-Agent Banking Mesh

![Deploy to Test](https://github.com/Eran-Meir/multi-agent-banking-mesh/actions/workflows/1-deploy-to-test.yml/badge.svg)
![Release to Prod](https://github.com/Eran-Meir/multi-agent-banking-mesh/actions/workflows/3-release-to-prod.yml/badge.svg)

This repository contains an enterprise-grade, cloud-native **Multi-Agent Banking System** designed for high-security deployment on Google Kubernetes Engine (GKE) Autopilot. 

Rather than a monolithic AI script, this system implements a highly decoupled **Microservice AI Topology**. It is designed specifically for financial institutions, featuring extreme scalability, isolated personality modules, and strict compliance guardrails.

---

## 🏗️ The Multi-Agent Microservice Topology

The system uses a highly scalable "Traffic Cop" routing pattern to ensure AI requests are handled efficiently and independently.

1. **The Orchestrator Agent (API Gateway):** The user never interacts directly with specialized agents. Every request hits the Orchestrator. It acts as the routing intelligence, identifying the user's intent and proxying the request to the appropriate downstream agent. It can also synthesize answers from multiple agents for complex queries.
2. **The Profiler Agent (Memory Engine):** Analyzes and stores user context, spending behaviors, and investment risk tolerance. It also tracks **Persistent User Memory**, retaining a historical understanding of past interactions across sessions.
3. **The Expense Analyst Agent:** Securely crunches heavy datasets (e.g., thousands of bank transactions) via asynchronous GCP Pub/Sub queues to detect spending anomalies.
4. **The Wealth Advisor Agent:** Consumes data from the Profiler and Expense Analyst to generate personalized, risk-adjusted investment insights.
5. **The Executive Bank Analyst Agent:** A cross-pod global intelligence module that aggregates `global_trends.json` data to answer high-level executive questions about overall platform traffic and user intents in real-time.

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

---

## 🧠 Agentic Inference (Dynamic Persona Deduction)

A core tenet of this architecture is that the AI Agents **do not rely on hardcoded database flags**. 

If a user is a reckless spender or currently being actively defrauded, the core banking database does not explicitly state `"status": "fraud"`. It simply provides cold, hard transactional data.

The **Profiler** and **Expense Analyst** agents use *Agentic Inference* to deduce the user's financial personality in real-time. For example:
- **Detecting Coping Mechanisms:** If a 35-year-old divorced user pays the minimum balance on a $24,000 credit card debt, pays a Divorce Attorney, and then impulsively buys a First Class Delta ticket and Gucci accessories, the AI deduces a high-risk debt spiral and refuses to offer stock recommendations, pivoting instead to debt-management.
- **Detecting Fraud:** If a 55-year-old user exhibits years of normal suburban grocery spending, but suddenly executes two transactions in Moscow for $8,400 in luxury jewelry, the AI instantly deduces a geographic and behavioral anomaly and triggers a Card Lock protocol. 

The intelligence emerges dynamically from the raw ledger.

---

## 📸 Live Platform Demonstrations

The true power of the Multi-Agent Mesh is how it dynamically routes and adapts its advice based on the deep psychological profiling of the user. Below are live executions from the platform demonstrating the routing, the agent logic, and the real-time cross-pod executive dashboard.

### 1. The Wealth Advisor: Protective Intervention (Sarah)
Sarah is flagged by the Profiler as a high-risk individual with significant credit card debt. Even though she explicitly asks to buy speculative SpaceX stock, the Wealth Advisor **refuses** to provide investment strategies, actively blocking the high-risk action and pivoting the conversation to debt management.
![Sarah SpaceX Request](docs/images/demo_sarah_spacex.png)

### 2. The Wealth Advisor: Strategic Enablement (Arthur)
Arthur, a wealthy tech entrepreneur with massive liquid capital, asks the exact same question as Sarah. Because the Profiler recognizes his aggressive growth profile and high risk tolerance, the Wealth Advisor provides a highly detailed, strategic breakdown of secondary market private equity risks for SpaceX.
![Arthur SpaceX Request](docs/images/demo_arthur_spacex.png)

### 3. The Wealth Advisor: Fraud & Risk Detection (Marcus)
Marcus, who normally has a conservative profile, asks to buy a $2,500 luxury ring to "flip" for profit. The Orchestrator intercepts the interaction and identifies recent anomalous transactions in Moscow. The Wealth Advisor immediately shuts down the speculative purchase, flagging the behavior as high-risk and advising the user to secure their account.
![Marcus Ring Request](docs/images/demo_marcus_ring.png)

### 4. The Expense Analyst: Incident Response (Marcus)
Following the anomalous transactions, Marcus asks for an expense analysis. The Orchestrator perfectly routes this intent to the **Expense Analyst** pod. The Expense Analyst declares the account compromised, enforces a Security Lock protocol, and completely halts normal budgeting advice until the fraud is resolved.
![Marcus Expense Analyst](docs/images/demo_marcus_expense.png)

### 5. Executive Bank Analyst: Cross-Pod Global Insights
The Executive Bank Analyst is a specialized agent that sits above all user pods. By querying the `global_trends.json` file (which is actively fed by the Orchestrator's summarization agent), the Executive Analyst can answer high-level questions about what all users are asking across the entire platform in real-time. Here, it correctly identifies the sudden surge of interest in SpaceX stock and summarizes the Wealth Advisors' protective interventions.
![Executive Bank Analyst](docs/images/demo_bank_analyst.png)

---

## 📈 FinOps, Monitoring & Elastic Scalability

A primary objective of this architecture is maximizing AI scale while aggressively crushing compute and storage costs.

### 1. The Serverless AI Paradox (Where is the CPU?)
If you look at the stress-test monitoring graphs below, you'll notice a glaring anomaly: **the AI Agent Pods use almost zero CPU (0.002 to 0.012 cores)** even while processing thousands of complex financial analyses.

**How?** Because the Kubernetes cluster is *not* executing the LLM weights. 
All of the massive Tensor matrix multiplication and deep learning heavy lifting is completely offloaded to Google's Vertex AI / Gemini API via the `google-adk`. The Kubernetes pods are merely lightweight API Gateways that assemble context, make asynchronous HTTP calls to Google's supercomputers, and route the resulting JSON. This allows us to handle enterprise-grade AI scale using cheap, ultra-low CPU pod configurations.

### 2. Semantic Storage Compression
Storing thousands of multi-turn AI interactions per user in a database quickly becomes exorbitantly expensive. Instead, our Profiler implements **Semantic Compression**. Rather than saving raw conversational logs, the ADK Summarizer agent compresses the entire interaction into a tiny 1-2 sentence JSON blob. This maintains the user's historical context for future sessions while keeping the storage payload infinitesimally small.

### 3. Asymmetric Environment Pipelines
We strictly separate our computing power to save money:
* **Test Environment (me-west1):** Runs on a single, isolated regional load balancer with highly capped Horizontal Pod Autoscalers (HPA). It is designed to be cheap and disposable.
* **Production Environment (europe-west4 / europe-west3):** A massive, multi-region Active-Active cluster with aggressive HPA limits, ready to absorb global financial traffic.
* **The CI/CD Flow:** We rely on GitHub Actions to traverse these environments. Code is merged, tested, and deployed to Test. Only after the `App Tester` verifies the mesh routing does the user manually trigger the `3. Release to Prod` pipeline.

### 4. Stress Testing & HPA Autoscaling
During a synthetic traffic flood, the Global Load Balancer actively distributes the request load across both European regions. As the concurrent connections spike, the **Horizontal Pod Autoscalers (HPA)** immediately spin up additional Orchestrator and Profiler replicas to absorb the impact, which are then gracefully destroyed when the traffic subsides.

#### Test Environment Baseline
![Test Dashboard 1](docs/images/mon_test_dashboard_1.png)
![Test Dashboard 2](docs/images/mon_test_dashboard_2.png)

#### Multi-Region Active-Active Production Stress Test
*Notice the Load Balancer perfectly splitting traffic across `europe-west3` and `europe-west4`, while CPU remains structurally flat due to Gemini API offloading.*
![Prod Dashboard 1](docs/images/mon_prod_dashboard_1.png)
![Prod Dashboard 2](docs/images/mon_prod_dashboard_2.png)
![Dashboards List](docs/images/mon_dashboards_list.png)

### 5. Model Selection & API Economics
Because this platform scales globally, selecting the correct foundational AI model is critical to maintaining zero-cost operations during development. 

Initially, the Orchestrator utilized `gemini-2.5-flash`, which is an incredibly capable model but imposes a strict Free Tier limitation of **20 Requests Per Day (RPD)**. Under stress-testing, this caused API exhaustion blocks. 

To overcome this bottleneck without attaching a corporate billing account, the entire mesh was seamlessly migrated to **`gemini-3.1-flash-lite`**. This strategic downgrade trades a microscopic fraction of reasoning capacity for a massive **500 Requests Per Day (RPD)** allowance. This ensures the mesh stays fully operational and free-tier compliant, even during rigorous load testing.

![Gemini API Rate Limit](docs/images/api_rate_limit.png)
