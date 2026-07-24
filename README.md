# CVEFixesUtil

Tooling to turn the [CVEfixes](https://github.com/secureIT-project/CVEfixes) vulnerability-fix database into
function-level *vulnerable / fixed* pairs, and to benchmark open-weight code LLMs on detecting the vulnerability
in those pairs.

The repository covers the full loop: extract pairs from the CVEfixes SQLite dump → filter to high-impact CWEs →
render prompts from a library of prompt strategies → run batched local inference with vLLM → score the answers
into TP/FP/TN/FN and derived metrics.

## What it does

1. **Dataset construction** (`main.ipynb`) — joins the CVEfixes tables (`file_change`, `commits`, `fixes`,
   `cwe_classification`, `method_change`), keeps method-level changes where the same method exists both before and
   after the fix, and exports per-language CSVs (C, C++, Python, Java, Ruby, Go).
2. **CWE selection** (`analysis.ipynb`) — maps each CVE's CWE list onto the MITRE Top-25, filters to the CWEs with
   enough pairs to evaluate, and produces the evaluation split used by the experiments.
3. **Prompt library** (`prompt.py`, `prompts_kat.py`) — three prompt families over the same detection task:
   `S*` standard/zero-shot, `R*` reasoning/step-decomposed, `D*` definition-augmented (CWE name + MITRE description
   injected). Variants differ in whether the CWE hint sits in the user prompt or the system prompt.
4. **Experiment runner** (`kat_vllm_experiment.py`, `kat_vllm_pipeline.py`) — runs one prompt family × one model over
   the split, batching `func_before` and `func_after` together so each pair is scored under identical decoding
   settings, and writes `kat_res/res_<EXP>_<model>.csv`.
5. **Answer extraction & scoring** (`evaluation1.py`, `utils.py`) — free-form model output often refuses the
   Yes/No format, so unparsable rows are re-asked with a short extraction prompt before being counted. Scoring is
   deliberately paired: a `func_before` "yes" is a TP, the *same* "yes" on `func_after` is an FP.

## Why it matters for vulnerability / code-LLM research

The before/after pair is the point. A detector that answers "yes, vulnerable" to everything scores well on a
vulnerable-only test set; on paired data it scores TP ≈ FP and its accuracy collapses to ~0.5. The measured results
in [`kat_experiment.md`](kat_experiment.md) show exactly that failure mode across all four evaluated models — e.g.
`D1_llama3` reaches 0.988 recall at 0.498 accuracy, and the best configuration overall (`R2_llama3`) still only
reaches 0.578 accuracy / 0.599 F1. The setup makes prompt-strategy claims falsifiable: same pairs, same decoding,
only the prompt changes.

Also useful as a worked example of the unglamorous parts — CVEfixes schema joins, CWE list flattening, and the
answer-extraction pass needed before any metric is trustworthy.

## Architecture

```
CVEfixes.db (Zenodo)
      │
      ├─ main.ipynb ────────────► CVEFixes_<lang>.csv        # method-level before/after pairs
      │                             │
      ├─ analysis.ipynb ────────────┴──► vulC7_test.csv       # Top-25 CWE evaluation split
      │                                    │
      │   prompts_kat.py ── S/R/D prompts ─┤
      │   assets/cwe25.json ── CWE names + descriptions
      │                                    ▼
      ├─ kat_vllm_pipeline.py ──► kat_vllm_experiment.py ──► kat_res/res_<EXP>_<model>.csv
      │        (model loop)          (vLLM batch inference)        │
      │                                                            ▼
      └─ evaluation1.py ──► re-ask unparsable answers ──► utils.calculate_metrics ──► kat_experiment.md
```

`utils.py` is the inference layer: `inferModelVllm` / `inferSystemModelVllm` for offline vLLM batches,
`inferModel` / `inferSystemModel` for an OpenAI-compatible HTTP endpoint (text-generation-webui), and `template()`
to apply the right chat format per model family (`llama3`, `codeqwen`, `deepseekcoder`, `artigenz`).

## Installation

```bash
git clone https://github.com/euisuh/CVEFixesUtil.git
cd CVEFixesUtil
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

`vllm` and `torch` are only needed to run inference; the notebooks and the prompt library import fine without them.
Inference assumes a CUDA GPU with enough memory for a 7B model at `dtype=half`, `max_model_len=8192`.

Then fetch the dataset:

1. Download `CVEfixes.db` from [Zenodo](https://zenodo.org/records/7029359) (v1.0.7).
2. Place it at `assets/CVEfixes.db`.
3. Put `cwe25.json` (MITRE Top-25 id / name / description) in `assets/` as well.

`assets/` is git-ignored — the database is several GB and is redistributed by its original authors.

## Quickstart

Render a prompt without any model or database — this is the fastest way to see what the pipeline feeds an LLM:

```bash
python -c "
from prompts_kat import promptS1, promptD1
print(promptS1('int f(char *s){ char b[8]; strcpy(b, s); }', 'Out-of-bounds Write'))
"
```

Check the paired scoring rule (`1` = model said "vulnerable", `0` = not, `-1` = unparsable):

```bash
python -c "
import pandas as pd; from utils import calculate_metrics
df = pd.DataFrame({'pred_before': [1, 0, -1], 'pred_after': [1, 0, -1]})
print(calculate_metrics(df, 'pred_before', 'pred_after'))  # (tp, fp, tn, fn, na_b, na_a) = (1, 1, 1, 1, 1, 1)
"
```

Both snippets run with only `pandas` installed — no GPU, no database. They are what CI executes on every push.

## Example workflow

```bash
# 1. Build pairs and the evaluation split (run main.ipynb, then analysis.ipynb)
#    -> assets/vulC7_test.csv

# 2. Run one prompt family across the configured models
python kat_vllm_pipeline.py --cuda-visible-devices 0 --experiment-name S1

# 3. Or run a single model / family directly
python kat_vllm_experiment.py \
    --cuda-visible-devices 0 \
    --experiment-name D2 \
    --model llama3 \
    --model-path meta-llama_Meta-Llama-3-8B-Instruct/

# 4. Re-ask the rows whose answers could not be parsed as Yes/No
python evaluation1.py --cuda-visible-devices 0

# 5. Score -> the tables in kat_experiment.md
```

Experiment names: `S1`–`S3` (standard), `R1`–`R2` (reasoning), `D1`–`D2` (definition-augmented).

## Project structure

| Path | Role |
|------|------|
| `main.ipynb` | CVEfixes SQLite → per-language method-level before/after CSVs |
| `analysis.ipynb` | CWE mapping to MITRE Top-25, split construction, metric table generation |
| `prompt.py` | Early single-file prompt templates (`prompt0`–`prompt3`) |
| `prompts_kat.py` | Prompt library: `promptS1`–`S6`, `promptR1`–`R6`, `promptD1`–`D5` |
| `kat_vllm_experiment.py` | Per-experiment runner (`expS1`…`expD2`), writes `kat_res/*.csv` |
| `kat_vllm_pipeline.py` | Loops the runner over a model list |
| `evaluation1.py` | Second-pass extraction of Yes/No from free-form answers |
| `utils.py` | vLLM + HTTP inference, chat templating, `calculate_metrics`, `extract_cwe` |
| `experiment.md` | Prompt templates for the first (`prompt0`–`prompt2`) experiment round |
| `kat_experiment.md` | Measured results: overall + per-CWE tables, before/after answer extraction |

## Author role

Repository owner and main contributor ([@euisuh15](https://github.com/euisuh15)) — ~68 of 75 commits. I built the
CVEfixes extraction and pair-construction pipeline (`main.ipynb`), the CWE selection and split logic
(`analysis.ipynb`), the vLLM inference and templating layer (`utils.py`), the experiment runner
(`kat_vllm_experiment.py`), the answer-extraction pass (`evaluation1.py`), and the scoring that produced the tables
in `kat_experiment.md`. The prompt library (`prompts_kat.py`) and parts of the multi-experiment pipeline were
contributed by [@CathrineShalby](https://github.com/CathrineShalby) and merged via PRs #1 and #3.

The published dataset derived from this pipeline is on Hugging Face:
[euisuh15/cveFixes1](https://huggingface.co/datasets/euisuh15/cveFixes1).

## Related work / citation

This repository is a downstream consumer of the CVEfixes dataset; please cite the original authors if you use it:

> Bhandari, G., Naseer, A., & Moonen, L. (2021). *CVEfixes: Automated Collection of Vulnerabilities and Their Fixes
> from Open-Source Software.* PROMISE '21. <https://github.com/secureIT-project/CVEfixes>

Dataset DOI (v1.0.7): <https://zenodo.org/records/7029359>. MITRE CWE Top-25 is used for CWE selection.

## Dataset coverage

Pairs per CWE in the extracted dataset, with the CWE's rank in the MITRE Top-25:

### C
| CWE ID | Name | Pairs | MITRE rank |
|--------|------|-------|------------|
| CWE-125| Out-of-bounds Read | 583 | 7 |
| CWE-119| Buffer Overflow | 493 | 17 |
| CWE-787| Out-of-bounds Write | 303 | 1 |
| CWE-20 | Improper Input Validation | 288 | 6 |
| CWE-476| NULL Pointer Dereference | 269 | 12 |
| CWE-416| Use After Free | 243 | 4 |
| CWE-190| Integer Overflow or Wraparound | 211 | 14 |
| CWE-362| Race Condition | 177 | 21 |

### Python
| CWE ID | Name | Pairs | MITRE rank |
|--------|------|-------|------------|
| CWE-918| Server-Side Request Forgery (SSRF) | 146 | 19 |
| CWE-352| Cross-Site Request Forgery (CSRF) | 121 | 9 |
| CWE-79 | Cross-Site Scripting | 63 | 2 |
| CWE-20 | Improper Input Validation | 61 | 6 |
| CWE-22 | Path Traversal | 51 | 8 |

### Java
| CWE ID | Name | Pairs | MITRE rank |
|--------|------|-------|------------|
| CWE-287| Improper Authentication | 126 | 13 |
| CWE-22 | Path Traversal | 101 | 8 |
| CWE-862| Missing Authorization | 62 | 11 |
| CWE-918| Server-Side Request Forgery (SSRF) | 48 | 19 |
| CWE-79 | Cross-site Scripting | 40 | 2 |

### Ruby
| CWE ID | Name | Pairs | MITRE rank |
|--------|------|-------|------------|
| CWE-89 | SQL Injection | 203 | 3 |
| CWE-79 | Cross-site Scripting | 65 | 2 |
| CWE-20 | Improper Input Validation | 54 | 6 |
| CWE-863| Incorrect Authorization | 30 | 24 |

### Go
| CWE ID | Name | Pairs | MITRE rank |
|--------|------|-------|------------|
| CWE-863| Incorrect Authorization | 36 | 24 |
| CWE-190| Integer Overflow or Wraparound | 19 | 14 |
| CWE-78 | OS Command Injection | 13 | 5 |
| CWE-918| Server-Side Request Forgery (SSRF) | 12 | 19 |
| CWE-22 | Path Traversal | 11 | 8 |
| CWE-20 | Improper Input Validation | 10 | 6 |

C++ pairs were extracted (`CVEFixes_c++.csv`) but were not tabulated per CWE.

## Limitations

- **Research code, not a library.** Paths are hardcoded (`assets/`, `kat_res/`, model weights under
  `../text-generation-webui/models/`); there is no packaging, CLI entry point, or config file.
- **Not reproducible end-to-end from a clean clone.** `assets/` and `kat_res/` are git-ignored, so the split
  (`vulC7_test.csv`), `cwe25.json`, and the raw model outputs are not in the repository — only the aggregated
  tables in `kat_experiment.md`.
- **Notebooks are exploratory.** `main.ipynb` and `analysis.ipynb` are linear working notebooks with dead cells
  and intermediate re-assignments; they document how the dataset was built rather than serving as a clean API.
- **`experiment.md` is a template, not results.** Its tables are placeholder `000` values from an earlier round;
  the measured numbers live in `kat_experiment.md`.
- **Detection labels are commit-derived.** A function is "vulnerable" because it precedes a CVE-linked fix commit;
  the fixed version may still contain other, unrelated vulnerabilities, so FP counts are an upper bound on real
  false positives.
- **Answer extraction is itself an LLM step.** Unparsable outputs are re-asked to Llama-3-8B-Instruct, which
  introduces its own error into the final counts.
- **`promptS2` contains a stray literal** (`process_name(data['name']` appended after the code block) — an artifact
  of the original run, kept so the published `S2` numbers stay reproducible.
- **Evaluated models are 7–8B open weights** (llama3, codeQwen, deepSeekCoder, artigenz) at temperature 0; results
  do not speak to larger or frontier models.
