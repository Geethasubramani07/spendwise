# Software Requirements Specification: SpendWise (draft v1)

Draft to start from. Handbook task 1.4 asks you to compare an AI-drafted SRS (v1) with your hand-corrected one (v2): edit this file into v2 and record what you changed.

## 1. Purpose
Students cannot track spending or notice suspicious transactions. SpendWise imports transactions, categorises them, enforces monthly budgets and flags anomalies.

## 2. Users
* **Individual user**: imports transactions, views the monthly report, sets budgets, reviews alerts.
* **Admin**: clears data and re-runs analysis (token-protected).

## 3. Functional requirements
| ID | Requirement |
|---|---|
| FR-1 | Import transactions from CSV (`date,description,amount`); reject files missing columns; skip invalid rows and report the count. |
| FR-2 | Ignore duplicate transactions (same time, description, amount). |
| FR-3 | Categorise each transaction into Food, Transport, Shopping, Bills, Entertainment, Health, Education or Other. |
| FR-4 | Let the user set a monthly limit per category; mark "warning" at >= 80% and "exceeded" above 100%. |
| FR-5 | Flag anomalous transactions using an Isolation Forest and show a plain-language reason for each alert. |
| FR-6 | Show a monthly report: total, per-category spend vs budget, 6-month trend, alert count. |
| FR-7 | Provide a demo data loader using synthetic data. |
| FR-8 | Admin-only actions (reset, re-analyse) require a token. |

## 4. Non-functional requirements
| ID | Requirement |
|---|---|
| NFR-1 | Categorisation accuracy >= 85% on held-out synthetic data. |
| NFR-2 | Fraud recall >= 70% on injected anomalies. |
| NFR-3 | Automated test coverage >= 80%. |
| NFR-4 | Upload limit 2 MB; max 50,000 rows. |
| NFR-5 | No real financial data; secrets in environment variables, never in Git. |
| NFR-6 | Dashboard renders user text safely (no HTML injection). |

## 5. Assumptions and open questions (check these by hand for task 1.4)
* Currency is INR; one user per installation.
* Amounts are positive spends; refunds/credits are not modelled.
* Alert thresholds (contamination 5%) are tuned on synthetic data.
* Ambiguity to resolve: what should happen when a transaction is re-categorised by the user? (Not implemented.)

## 6. Process model (task 1.1 starting point)
Iterative/Agile (Scrum, 1-week sprints) fits a small team and changing ML requirements; justify or change this in your report.
