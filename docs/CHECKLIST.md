# Sentinel — 7-Day Build Checklist

Track progress as you ship. Cross off as you go.

## Day 1-2 — Data + Model
- [ ] Download IEEE-CIS dataset → `data/`
- [ ] Run `notebooks/01_eda.py` (or paste into Jupyter), 2hr cap
- [ ] Run `python -m src.training.train`
- [ ] Verify AUC ≥ 0.92 in `models/metrics.json`
- [ ] Commit `models/feature_names.json` and `models/metrics.json` (NOT the `.joblib`)

## Day 3 — FastAPI + Docker
- [ ] `uvicorn src.api.main:app --reload` → hit `http://localhost:8000/docs`
- [ ] Test `/predict` with sample txn (use the Streamlit dashboard's SAMPLE)
- [ ] `docker build -t sentinel-api .`
- [ ] `docker compose up` → both API and dashboard running

## Day 4-5 — LangGraph Agent
- [ ] `python -m src.agent.seed_db` → SQLite populated
- [ ] `python -m src.agent.graph` → smoke test prints fallback explanation
- [ ] Test `/investigate` endpoint via Streamlit (works without AWS using fallback)
- [ ] Once AWS creds set: verify Bedrock call succeeds

## Day 6 — AWS Deploy
- [ ] Follow `docs/DEPLOYMENT.md`
- [ ] Push image to ECR
- [ ] Request Bedrock model access (Claude 3.5 Sonnet)
- [ ] Create task definition + service on Fargate behind ALB
- [ ] Test public `/health` endpoint
- [ ] Test `/investigate` with Bedrock live

## Day 7 — Polish
- [ ] Add `AWS_ROLE_ARN` secret to GitHub repo
- [ ] Push to `main` → CI runs lint + tests, builds + pushes image, redeploys ECS
- [ ] Architecture diagram (draw.io / Excalidraw) → save as `docs/architecture.png`
- [ ] Update README with screenshot of dashboard
- [ ] Record 3-min Loom: problem → architecture → live demo → tradeoffs
- [ ] Add Loom link to top of README

## Stretch (only if ahead of schedule)
- [ ] Add SHAP for proper feature attribution (replace `_top_features`)
- [ ] Add a Jupyter notebook showing model explainability
- [ ] Add Locust/k6 load test (`scripts/load_test.py`)
