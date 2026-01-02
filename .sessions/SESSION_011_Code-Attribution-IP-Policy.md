# SESSION_011: Code Attribution & Intellectual Property Policy

**Date**: 2026-01-02  
**Status**: Active  
**Trigger**: User request to document code attribution best practices

---

## Objective

Codify code attribution, licensing, and intellectual property practices as **ADR-0049** to fill documented gap referenced in DISC-015.

---

## Scope

- Create ADR-0049 for Code Attribution & IP Policy
- Update `.adrs/INDEX.md`
- Review AGENTS.md for IP guidance integration

---

## User Requirements

User provided comprehensive statement covering:

1. **In-code attribution**: Comments/docstrings with citations
2. **LICENSE/NOTICE files**: Third-party attribution
3. **README/docs**: Architectural influences
4. **Version control**: Tagged commits with references
5. **Best practices**: License checking, no plagiarism, peer review, CI scanning

---

## Actions Taken

1. ✅ Analyzed existing documentation for IP/attribution guidance
2. ✅ Confirmed ADR-0049 gap (referenced but not created)
3. ✅ Created ADR-0049 with user-provided best practices
4. ✅ Updated ADR INDEX
5. ✅ Integrated attribution requirement into AGENTS.md Rule 11
6. ✅ Added legal compliance to Solo-Dev Principles summary

---

## Key Findings

- **DISC-015** mandates research code citations → ADR-0049 (pending)
- **No existing ADR** covers code attribution or IP practices
- User statement aligns with existing quality principles (Rule 0, 10, 11)
- Statement adds enterprise-grade compliance guidance (NOTICE files, license scanning)

---

## Handoff Notes

ADR-0049 will establish:

- 4-tier attribution system (in-code, LICENSE, docs, git)
- License compliance workflow
- AI-generated code vetting policy
- Model card requirements for ML artifacts
