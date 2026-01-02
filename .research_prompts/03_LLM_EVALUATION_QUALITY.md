# Research Prompt: LLM Evaluation & Quality Scoring

> **Priority**: P4 (MEDIUM)
> **Addresses**: W3 (Quality Scoring Implementation)
> **Current Score**: 4/10

---

## Research Goal

Find papers on using LLMs as judges, automated evaluation of generated content, quality rubrics for code/documentation, and calibration techniques.

---

## Search Queries

### For arXiv / Semantic Scholar / Google Scholar:

```
1. "LLM as judge" evaluation
2. "automated evaluation" code quality
3. "MT-Bench" "AlpacaEval" methodology
4. "self-evaluation" language models
5. "quality rubrics" generated text
6. "calibration" LLM confidence
7. "documentation quality" metrics automated
8. "code review" automation LLM
9. "pairwise comparison" LLM evaluation
10. "reward modeling" code generation
```

### For Software Engineering Venues:

```
1. Automated code review using large language models
2. Quality metrics for AI-generated code
3. Documentation quality assessment automation
4. Continuous evaluation of generative AI outputs
5. Human-AI agreement in code evaluation
```

---

## Specific Topics Needed

### 1. LLM-as-Judge Patterns

- Single-point scoring vs pairwise comparison
- Reference-based vs reference-free evaluation
- Multi-aspect evaluation (correctness, style, completeness)
- Judge model selection (which models are good judges?)

### 2. Calibration & Reliability

- Consistency across multiple evaluations
- Bias detection and mitigation
- Confidence scoring accuracy
- Human-AI correlation studies

### 3. Code-Specific Evaluation

- Functional correctness metrics
- Style and convention adherence
- Security vulnerability detection
- Performance considerations

### 4. Documentation Evaluation

- Completeness rubrics
- Clarity and readability scores
- Consistency with code
- Audience appropriateness

### 5. Rubric Design

- How to specify evaluation criteria?
- Weighting multiple dimensions
- Examples and few-shot prompting
- Rubric versioning and evolution

---

## Target Venues

- **ACL/EMNLP** - Evaluation methodology tracks
- **NeurIPS** - Benchmarks and evaluation
- **ICSE/FSE** - Software quality
- **ISSTA** - Software testing
- **arXiv cs.CL** - NLP evaluation papers
- **arXiv cs.SE** - Software engineering

---

## Keywords for Filtering

```
LLM evaluation, LLM as judge, automated evaluation, quality metrics,
code quality, documentation quality, calibration, confidence scoring,
MT-Bench, AlpacaEval, pairwise comparison, rubric, self-evaluation,
code review, automated assessment, benchmark, quality scoring
```

---

## Key Papers to Find (if available)

- Judging LLM-as-a-Judge with MT-Bench
- AlpacaEval methodology papers
- G-Eval: NLG Evaluation using GPT-4
- Self-Refine: Iterative Refinement with Self-Feedback
- Constitutional AI evaluation approaches
- HumanEval / MBPP benchmark papers
- CodeBLEU and code-specific metrics

---

## Expected Paper Count

Target: **8-12 papers** covering:

- 2-3 on LLM-as-judge methodology
- 2-3 on calibration and reliability
- 2-3 on code quality evaluation
- 1-2 on documentation assessment
- 1-2 surveys on LLM evaluation

---

## After Acquisition

1. Extract with: `python scripts/extract_pdf_papers.py --batch llm-evaluation <pdfs>`
2. Ingest with: `python scripts/research_paper_cli.py ingest ... --category llm-evaluation`
3. Update vision based on findings
