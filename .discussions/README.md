# Discussions (DISC)

> **Part of**: AI Coding Manager (AICM)
> **Purpose**: Refine chat conversations into structured problem explorations.

---

## The Chain

```
Chat Log → DISC → ADR → SPEC → Contract → Code → Traces → Knowledge
```

**Every DISC must trace to a source chat log.** This is the Genesis principle.

---

## Creating a DISC

1. Identify a chat log with a significant topic (`.chat_logs/`)
2. Extract the problem being discussed
3. Create `DISC-NNN_{Topic}.md` using the template
4. Set `Source Chat:` to the originating chat log file

---

## Numbering

DISCs are numbered sequentially: `DISC-001`, `DISC-002`, etc.

Check existing DISCs before creating a new one.

---

## Status Values

| Status | Meaning |
|--------|---------|
| `draft` | Work in progress |
| `active` | Under discussion |
| `resolved` | Decision made, artifacts produced |
