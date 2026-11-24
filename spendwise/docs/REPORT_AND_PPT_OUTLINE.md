# Report and PPT outline (from the handbook templates)

## Report chapters
1. **Introduction**: problem, users, objectives, scope.
2. **Introduction to AI in SE** (Phase 1): SRS with AI, process model, screens + API contract, API generated with prompts. Evidence tables 1.1-1.6.
3. **Agile practices and AI planning** (Phase 2): Jira stories/sprints, Scrum events, XP + Kanban, estimation AI vs team. Tables 2.1-2.8.
4. **Development and deployment with AI tools** (Phase 3): prompt library, categoriser + Isolation Forest, Git workflow, Docker/CI/Jenkins. Tables 3.1-3.8.
5. **AI-based testing and monitoring** (Phase 4): unit tests for budget rules, import-to-alert integration tests, Selenium dashboard test, AI test prioritisation, alert-latency monitoring. Tables 4.1-4.9.
6. **AI-powered QA and ethics** (Phase 5): SonarQube + AI security review, SQA plan, bias and false-alarm cost, privacy checklist. Tables 5.1-5.6.
7. **Integration and results**: architecture, end-to-end results vs targets (accuracy 85%, recall 70%, coverage 80%).
8. **Responsible AI reflection**: synthetic data, encrypted/secret handling, explained alerts, AI-usage log.
9. **Conclusion and future work**: outcomes, limitations, two improvements (e.g. user accounts with login, per-user models).
Appendices: prompt log, code links, screenshots.

## Architecture (for the report and slide 3)
Browser dashboard -> FastAPI (`app/main.py`) -> service layer (`import`, `budgets`, `reports`) -> SQLite; categoriser (rules + TF-IDF/LogReg) and fraud detector (Isolation Forest) are called during import.

## PPT: 12 slides, 6 minutes
1 Title | 2 Problem and users | 3 Architecture | 4 Phase 1 | 5 Phase 2 | 6 Phase 3 | 7 Phase 4 | 8 Phase 5 | 9 Demo (load demo data, show an alert with its reason, set a budget) | 10 Results chart + table vs targets | 11 Responsible AI | 12 Conclusion, Q&A, repo QR code.

## Demo script (3 minutes)
1. `uvicorn app.main:app`, open the dashboard.
2. Load demo data; point out KPIs and the category bars.
3. Open a fraud alert and read the "Why flagged" reason.
4. Set Food budget low; show the budget alert.
5. Show `pytest` and `python scripts/evaluate.py` output.
