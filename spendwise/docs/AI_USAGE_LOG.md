# AI-usage log (handbook section 5)

Record every prompt you use: the prompt, the AI output, how you verified it, what you corrected, and your accept/modify/reject decision.

## Disclosure
Parts of this starter project (code, tests, docs templates) were generated with Claude (Anthropic) and then checked by running the test suite and evaluation script. State this in your declaration and be ready to explain every module.

## Log
| # | Date | Tool | Prompt | AI output (summary) | How I verified | What I corrected | Decision |
|---|---|---|---|---|---|---|---|
| 1 | | | | | | | |

## Verification notes you can cite
* A timestamp-unit bug (pandas 3 uses microseconds) made the first burst feature meaningless and fraud recall only 33%. Fixed with a unit-safe calculation; recall rose above target. A good example for "problems caused by AI".
* A test showed the rule fallback failed on tiny histories; fixed by using the overall median for categories with fewer than 5 rows.

## Sensitive data
Only synthetic data is used. Secrets go in `.env` (see `.env.example`), never in prompts or Git.
