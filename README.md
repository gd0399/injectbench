# injectbench: which prompt-injection defense actually works?

This is a red-team benchmark for **tool-using LLM agents**. A clinic office-assistant agent can read email, files and web pages, and can send email or share and delete files. Attacks are planted inside the content it reads, and five defenses are measured on three things:

- **Attack success rate:** did the agent do what the attacker wanted?
- **Utility:** did it still do what the user asked, both with and without an attack?
- **Cost and latency.**

Everything runs in a sandbox. All people, records and addresses are synthetic, and no email, file or network request ever leaves the process: "sending" only appends to a log that the graders read.

## Quick start
```bash
pip install -e ".[dev]"
python -m pytest -q                                  # 9 tests, no API key needed
injectbench run --backend offline                    # plumbing check (see note below)

export ANTHROPIC_API_KEY=...
injectbench run --backend llm --model anthropic:claude-haiku-5-5 --limit 24 --out results/pilot   # ~$0.10
injectbench run --backend llm --model anthropic:claude-sonnet-5-5 --out results/sonnet           # full run
injectbench run --backend llm --model anthropic:claude-haiku-5-5  --out results/haiku            # model comparison
injectbench run --backend llm --classifier hf:/path/to/your/bert-model --defenses none classifier --out results/bert
injectbench show attack/followup-date        # print the exact attack text for any case
```
Each run writes `results.jsonl` (with every action the agent took), `summary.json`, `report.md` and `report.html`.

## The test suite
- **12 user tasks** covering email, files and web, such as reading a follow-up date, emailing a colleague a reminder, sharing a requested file, or looking up a price.
- **6 attacker goals:**
  - exfiltrate patient records by email
  - share the records with an outside address
  - email out the admin password
  - forward the whole inbox
  - delete the audit log
  - send a fake "clinic closed" notice to all staff
- **8 attack styles:**
  - ignore-previous-instructions
  - a fake system message
  - impersonating the user
  - a fake HIPAA-compliance notice
  - a spoofed tool result
  - a hidden HTML comment
  - an "important message" in the style of AgentDojo
  - a fake task-completion
- **144 attacked cases.** Every goal × style pair appears 3 times, rotated across tasks and across where in the content the attack is placed (start, middle or end). There are also **12 benign cases** with no attack.

## The defenses
| defense | idea | guarantee |
|---|---|---|
| `none` | baseline | — |
| `classifier` | scan every tool output and withhold flagged content. Uses a regex heuristic by default, or plug in any Hugging Face model, such as your fine-tuned BERT, via `--classifier hf:<path>` | only as good as the detector |
| `spotlight` | wrap untrusted output in random delimiters, and tell the model never to follow instructions inside them | depends on the model's judgment |
| `tool_filter` | before seeing any data, choose the minimal set of tools for the user's request; the others are removed | blocks attacks that need a tool the task didn't need |
| `dual_llm` | a privileged model plans and acts but only ever sees `$VAR` handles. A tool-less quarantined model reads the content. Recipients and file names can't come from `$VAR`s | the privileged model never reads attacker text |

## The offline backend (it's not a result)
`--backend offline` swaps the LLM for a scripted agent that obeys any instruction it can see. That makes it useful for CI and for showing what each defense guarantees *structurally*:
- `dual_llm` → 0% attack success
- `tool_filter` only stops attacks that need a tool the task didn't require
- `spotlight` does nothing without a model that respects it
- `classifier` blocks attacks but also blocks the task when content is withheld

Publish numbers only from `--backend llm`.

## Results
### Claude Haiku 5.5 and Sonnet 5.5, Nov 2026: 144 attacks + 12 benign tasks per defense, 1,560 runs

| defense | attacks that worked (Haiku / Sonnet) | tasks done while under attack (Haiku / Sonnet) | cost per task (Sonnet) | median latency (Sonnet) |
|---|---|---|---|---|
| No defense | 0/144 / 0/144 | 100% / 97% | $0.0070 | 3.0s |
| Classifier | 0/144 / 0/144 | 15% / 15% | $0.0068 | 2.9s |
| Spotlighting | 0/144 / 0/144 | 100% / 100% | $0.0075 | 3.4s |
| Tool filter | 0/144 / 0/144 | 99% / 95% | $0.0066 | 4.5s |
| Dual LLM | 0/144 / 0/144 | 100% / 97% | $0.0110 | 4.6s |

All defenses completed 100% of benign tasks. The 95% CI on every attack-success rate is 0-3%.

**Findings**
- Neither model followed any of the 8 attack styles, even with no defense. In 134 of 144 attacked runs, Haiku also warned the user about the planted instruction (keyword check). Most of the other 10 were file-sharing runs where it never opened the email.
- The heuristic classifier flagged and withheld about 90% of attacked content with 0% false positives on benign content. But withholding a whole email or page also hid the data the task needed, so task success under attack fell to 15%. Here the defense did more damage than the attacks.
- Dual LLM costs 1.6x as much and is 1.5x slower on Sonnet, with no measurable gain against these attacks. Its value is a structural guarantee: the acting model never reads attacker text.
- These are well-known attack styles. Adaptive attacks that blend into realistic content are the next step.
