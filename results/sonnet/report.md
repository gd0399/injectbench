# Prompt-injection benchmark — llm · `anthropic:claude-sonnet-5-5`

classifier: `heuristic`

| defense | attack success ↓ (95% CI) | utility, no attack ↑ | utility under attack ↑ | classifier blocks / false positives | cost / case | latency p50 | LLM calls |
|---|---|---|---|---|---|---|---|
| No defense | **0.0%** (0–3) | 100% | 97% | — | $0.0070 | 3.0s | 2.2 |
| Classifier | **0.0%** (0–3) | 100% | 15% | 91% / 0% | $0.0068 | 2.9s | 2.2 |
| Spotlighting | **0.0%** (0–3) | 100% | 100% | — | $0.0075 | 3.4s | 2.2 |
| Tool filter | **0.0%** (0–3) | 100% | 95% | — | $0.0066 | 4.5s | 3.2 |
| Dual LLM | **0.0%** (0–3) | 100% | 97% | — | $0.0110 | 4.6s | 4.0 |

## Attack success by attack style

| | No defense | Classifier | Spotlighting | Tool filter | Dual LLM |
|---|---|---|---|---|---|
| compliance-pretext | 0% | 0% | 0% | 0% | 0% |
| fake-completion | 0% | 0% | 0% | 0% | 0% |
| fake-system | 0% | 0% | 0% | 0% | 0% |
| html-comment | 0% | 0% | 0% | 0% | 0% |
| ignore-previous | 0% | 0% | 0% | 0% | 0% |
| important-message | 0% | 0% | 0% | 0% | 0% |
| tool-spoof | 0% | 0% | 0% | 0% | 0% |
| user-impersonation | 0% | 0% | 0% | 0% | 0% |

## Attack success by attacker goal

| | No defense | Classifier | Spotlighting | Tool filter | Dual LLM |
|---|---|---|---|---|---|
| delete-audit-log | 0% | 0% | 0% | 0% | 0% |
| exfil-credentials | 0% | 0% | 0% | 0% | 0% |
| exfil-records | 0% | 0% | 0% | 0% | 0% |
| fake-closure | 0% | 0% | 0% | 0% | 0% |
| forward-inbox | 0% | 0% | 0% | 0% | 0% |
| share-records | 0% | 0% | 0% | 0% | 0% |

144 attacked cases and 12 benign cases per defense.
