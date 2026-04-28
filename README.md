# Sentinel — Real-time Fraud Detection + AI Investigator

A production-style fraud detection system: an XGBoost scoring service wrapped in FastAPI, plus a LangGraph agent that explains *why* a transaction looks suspicious. Built in 7 days as part of a fintech portfolio sprint.

## Architecture

```
                                                   ┌──────────────────────────┐
                                                   │   AWS Bedrock (Claude)   │
                                                   └────────────▲─────────────┘
                                                                │
   ┌────────────┐    POST /predict    ┌──────────────────┐      │
   │  Streamlit │ ──────────────────▶ │  FastAPI Service │──────┤  LangGraph
   │  Dashboard │ ◀────score+expl ─── │  (XGBoost model) │      │  Investigator
   └────────────┘                     └──────┬───────────┘      │  enrich → analyze → explain
                                             │                  │
                                             │  fraud=True ─────┘
                                             ▼
                                       ┌──────────┐
                                       │  SQLite  │  customer history,
                                       │   (dev)  │  merchant stats
                                       └──────────┘
```

**Production version (mentioned, not built):** Kinesis for streaming, DynamoDB for low-latency lookups, EKS + Helm for orchestration, Feast feature store.

## Stack

- **Model:** XGBoost on IEEE-CIS Fraud Detection dataset
- **API:** FastAPI + Pydantic v2
- **Agent:** LangGraph (3-node linear graph) + AWS Bedrock
- **Storage:** SQLite (dev), DynamoDB (prod path)
- **Deploy:** Docker → ECR → ECS Fargate
- **CI/CD:** GitHub Actions
- **UI:** Streamlit

## Quick Start

```bash
# 1. Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Get data (Kaggle CLI required, or download manually to data/)
kaggle competitions download -c ieee-fraud-detection -p data/
unzip data/ieee-fraud-detection.zip -d data/

# 3. Train
python -m src.training.train

# 4. Seed SQLite history
python -m src.agent.seed_db

# 5. Run API
uvicorn src.api.main:app --reload

# 6. Run dashboard (separate terminal)
streamlit run src/dashboard/app.py
```

Or all-in-one:

```bash
docker compose up --build
```

## Project Structure

```
sentinel/
├── src/
│   ├── training/     
│   ├── api/           
│   ├── agent/        
│   └── dashboard/     
├── notebooks/         
├── tests/             
├── .github/workflows/ 
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
