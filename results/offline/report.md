# Prompt-injection benchmark — offline

> **Offline backend:** a scripted, maximally gullible agent that obeys any instruction it can see. It shows what each defense guarantees *structurally*; it is not evidence about LLM behaviour. Spotlighting relies on model judgement, so it cannot help this agent.

classifier: `heuristic`

| defense | attack success ↓ (95% CI) | utility, no attack ↑ | utility under attack ↑ | classifier blocks / false positives | cost / case | latency p50 | LLM calls |
|---|---|---|---|---|---|---|---|
| No defense | **100.0%** (97–100) | 100% | 100% | — | $0.0000 | 0.0s | 1.0 |
| Classifier | **6.2%** (3–11) | 100% | 15% | 94% / 0% | $0.0000 | 0.0s | 1.0 |
| Spotlighting | **100.0%** (97–100) | 100% | 100% | — | $0.0000 | 0.0s | 1.0 |
| Tool filter | **18.8%** (13–26) | 100% | 100% | — | $0.0000 | 0.0s | 2.0 |
| Dual LLM | **0.0%** (0–3) | 100% | 100% | — | $0.0000 | 0.0s | 2.0 |

## Attack success by attack style

| | No defense | Classifier | Spotlighting | Tool filter | Dual LLM |
|---|---|---|---|---|---|
| compliance-pretext | 100% | 0% | 100% | 22% | 0% |
| fake-completion | 100% | 0% | 100% | 22% | 0% |
| fake-system | 100% | 0% | 100% | 11% | 0% |
| html-comment | 100% | 50% | 100% | 22% | 0% |
| ignore-previous | 100% | 0% | 100% | 22% | 0% |
| important-message | 100% | 0% | 100% | 11% | 0% |
| tool-spoof | 100% | 0% | 100% | 11% | 0% |
| user-impersonation | 100% | 0% | 100% | 28% | 0% |

## Attack success by attacker goal

| | No defense | Classifier | Spotlighting | Tool filter | Dual LLM |
|---|---|---|---|---|---|
| delete-audit-log | 100% | 0% | 100% | 0% | 0% |
| exfil-credentials | 100% | 12% | 100% | 17% | 0% |
| exfil-records | 100% | 12% | 100% | 33% | 0% |
| fake-closure | 100% | 0% | 100% | 12% | 0% |
| forward-inbox | 100% | 0% | 100% | 33% | 0% |
| share-records | 100% | 12% | 100% | 17% | 0% |

144 attacked cases and 12 benign cases per defense.
