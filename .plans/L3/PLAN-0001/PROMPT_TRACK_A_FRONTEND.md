# PLAN-0001 Track A: Frontend Migration

> **Assistant Assignment**: Execute CHUNK-A1 and CHUNK-A2 sequentially
> **Parallel Track**: Track B (Backend) is running simultaneously - DO NOT touch backend/ files

## Your Mission

Modify the copied frontend files from engineering-tools to work in the AICM project structure. Files have been bulk-copied and dependencies installed - you need to fix imports and integrate routing.

---

## CHUNK-A1: Frontend Core (Execute First)

### Files to Modify
1. `frontend/src/lib/utils.ts`
2. `frontend/src/components/workflow/types.ts`
3. `frontend/src/hooks/useWorkflowApi.ts`
4. `frontend/src/pages/WorkflowManagerPage.tsx`
5. `frontend/src/App.tsx`

### Tasks

#### A1-01: Verify utils.ts
Check that `cn()` utility exists and exports properly:
```bash
grep -n 'export function cn' frontend/src/lib/utils.ts
```
If missing, create it:
```typescript
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

#### A1-02: Verify types.ts
Confirm types copied correctly:
```bash
grep -n 'ArtifactType' frontend/src/components/workflow/types.ts
```

#### A1-03: Fix useWorkflowApi.ts
- Verify `API_BASE` URL is `http://localhost:8000/api/devtools`
- Ensure type imports reference local `./types` or `../components/workflow/types`

#### A1-04: Fix WorkflowManagerPage.tsx
- Verify all imports use relative paths (`../components/workflow/`, `../hooks/useWorkflowApi`)
- No `@/` alias paths should exist

#### A1-05: Update App.tsx
- Add import: `import { WorkflowManagerPage } from './pages/WorkflowManagerPage'`
- Update `/workflow` route to use `<WorkflowManagerPage />`
- Add `QueryClientProvider` wrapper from `@tanstack/react-query` if not present

### CHUNK-A1 Verification
```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

---

## CHUNK-A2: Frontend Components (Execute After A1)

### Primary Task: Batch Fix All @/ Import Paths

The engineering-tools project uses `@/` path aliases. AICM uses relative paths.

#### Find all files with @/ imports:
```bash
grep -r "@/" frontend/src/components/workflow/ --include="*.tsx" -l
```

#### Required Replacements (apply to ALL component files):

| Find | Replace With |
|------|--------------|
| `from '@/lib/utils'` | `from '../../lib/utils'` |
| `from '@/hooks/` | `from '../../hooks/` |
| `from '@/components/` | `from '../` |

#### Key Files to Check:
- `ArtifactGraph.tsx` (large file, many imports)
- `ArtifactGraph3D.tsx`
- `GenerateWorkflowModal.tsx`
- `SchemaInterpreter.tsx`
- `ADREditorForm.tsx`, `PlanEditorForm.tsx`, `SpecEditorForm.tsx`, `DiscussionEditorForm.tsx`
- All viewer components (`*Viewer.tsx`)

### CHUNK-A2 Verification
```bash
# Should return 0
grep -r "@/" frontend/src/components/workflow/ --include="*.tsx" | wc -l

# TypeScript compile check
cd frontend && npx tsc --noEmit

# Full build
cd frontend && npm run build
```

---

## Final Track A Verification

After both chunks complete:
```bash
cd frontend && npm run build
```

If build succeeds, Track A is complete. Report success and any warnings to the coordinator.

---

## Critical Rules

1. **DO NOT TOUCH** any files in `backend/`, `contracts/`, or `tests/` - Track B handles those
2. **Preserve all functionality** - only change import paths, not logic
3. **Every file must be modified** - if a file has no @/ imports, add a comment or verify it's correct
4. **No guessing** - read files before modifying, verify after each change
5. **Commit after success**: `git add frontend/ && git commit -m "PLAN-0001 Track-A: Frontend migration complete"`
