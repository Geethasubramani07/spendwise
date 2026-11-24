# Evidence checklist (maps to the handbook's syllabus coverage tables)

The code supports these items, but the **evidence must be produced by you** (screenshots, logs, ratings). Nothing here is pre-filled on purpose; fabricated evidence would defeat the assessment.

## Phase 1 (Days 3-6)
| ID | What exists in this repo | What you still do |
|---|---|---|
| 1.1 | `docs/SRS.md` section 6 | Write the model comparison table; justify choice |
| 1.2 | none | Time one task manually vs with AI; log time/defects/effort |
| 1.3 | none | Same task in Copilot, Tabnine, ChatGPT; scorecard |
| 1.4 | `docs/SRS.md` (v1 draft) | Make v2 by hand; list ambiguities found |
| 1.5 | `app/service.py`, `app/categoriser.py` | Keep your prompt log; review line by line |
| 1.6 | `tests/` | Write test cases from requirements; record defects found/missed |

## Phase 2 (Days 7-10)
| ID | Repo support | You do |
|---|---|---|
| 2.1-2.5 | `docs/SRS.md` FRs as story seeds | Jira sprints, Scrum notes, Definition of Done, XP/Kanban observations |
| 2.6-2.8 | none | AI story points vs team poker; Jira AI screenshots; one-page evaluation |

## Phase 3 (Days 11-15)
| ID | Repo support | You do |
|---|---|---|
| 3.1-3.3 | `app/` code | Development diary; prompt library with 3 variants and ratings; accepted/edited/rejected log |
| 3.4 | none | Use feature branches, PRs with review, resolve one merge conflict |
| 3.5 | `.github/workflows/ci.yml` | Push to GitHub; screenshot green run and badge |
| 3.6 | `Jenkinsfile` | Run Jenkins (docker), add webhook; save console output |
| 3.7 | `Dockerfile`, `docker-compose.yml` | `docker compose up --build`; screenshot running container |
| 3.8 | none | Benefit/challenge table |

## Phase 4 (Days 16-19)
| ID | Repo support | You do |
|---|---|---|
| 4.1 | none | Run 15 manual cases, then automate; compare effort |
| 4.2 | `tests/test_budgets.py`, `test_categoriser.py`, `test_fraud.py` | `pytest --cov=app`; save report |
| 4.3 | `tests/test_import.py`, `test_api.py` | Save results |
| 4.4 | none | Write end-to-end and acceptance tests from user stories |
| 4.5 | `selenium_tests/test_dashboard.py` | Extend (import flow, budget form); save report |
| 4.6 | none | Ask AI for extra cases, rank by risk, run top first |
| 4.7 | none | Collect metrics/defect history; train a small defect model |
| 4.8 | `/api/health` | Add metrics endpoint + Prometheus/Grafana; track alert latency |
| 4.9 | `scripts/evaluate.py` | Summarise AI-testing false positives/gaps |

## Phase 5 (Days 20-23)
| ID | Repo support | You do |
|---|---|---|
| 5.1 | README metrics | SQA plan + radar chart of five quality attributes |
| 5.2 | none | `docker run -d -p 9000:9000 sonarqube:community`; scan; before/after |
| 5.3 | none | AI review of 3 modules vs SonarQube vs human |
| 5.4 | README "Known limitations" | Responsible-AI checklist (bias, privacy, transparency, accountability) |
| 5.5 | none | Write one module manually, compare; AI-usage declaration |
| 5.6 | none | Lessons page |

## Success metrics (reproduce with `python scripts/evaluate.py`)
Categorisation accuracy >= 85%; fraud recall >= 70%; coverage >= 80% (run `pytest --cov=app`).
