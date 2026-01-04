# Architecture Decision Records (ADR)

> **Part of**: AI Coding Manager (AICM)
> **Purpose**: Capture architectural decisions with context and rationale.

---

## The Chain

Every ADR must trace back to a DISC, which traces back to a chat log.

```
DISC-NNN → ADR-NNNN
```

---

## Creating an ADR

1. A DISC reaches a decision point
2. Create `ADR-NNNN_{Decision-Title}.md`
3. Set `Source DISC:` to the originating discussion
4. Document the decision, context, and consequences

---

## Numbering

ADRs are numbered sequentially: `ADR-0001`, `ADR-0002`, etc.

---

## Status Values

| Status | Meaning |
|--------|---------|
| `draft` | Under review |
| `accepted` | Decision is in effect |
| `superseded` | Replaced by newer ADR |
| `deprecated` | No longer applies |
