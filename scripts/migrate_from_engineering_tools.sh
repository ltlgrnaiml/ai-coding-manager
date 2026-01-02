#!/bin/bash
# PLAN-0001: Bulk Copy Script - Frontend Migration from Engineering-Tools
# Run from ai-coding-manager root directory
# Usage: bash scripts/migrate_from_engineering_tools.sh

set -e  # Exit on any error

SOURCE_ROOT="/home/mycahya/coding/engineering-tools"
TARGET_ROOT="/home/mycahya/coding/ai-coding-manager"

echo "=== PLAN-0001: Frontend Migration Bulk Copy ==="
echo "Source: $SOURCE_ROOT"
echo "Target: $TARGET_ROOT"
echo ""

# =============================================================================
# FRONTEND: Components, Hooks, Utils, Pages
# =============================================================================

echo "[1/6] Creating frontend directory structure..."
mkdir -p "$TARGET_ROOT/frontend/src/components/workflow"
mkdir -p "$TARGET_ROOT/frontend/src/hooks"
mkdir -p "$TARGET_ROOT/frontend/src/lib"
mkdir -p "$TARGET_ROOT/frontend/src/pages"

echo "[2/6] Copying workflow components (30+ files)..."
cp -r "$SOURCE_ROOT/apps/homepage/frontend/src/components/workflow/"* \
      "$TARGET_ROOT/frontend/src/components/workflow/"

echo "[3/6] Copying hooks..."
cp "$SOURCE_ROOT/apps/homepage/frontend/src/hooks/useWorkflowApi.ts" \
   "$TARGET_ROOT/frontend/src/hooks/"

echo "[4/6] Copying lib utilities..."
cp "$SOURCE_ROOT/apps/homepage/frontend/src/lib/utils.ts" \
   "$TARGET_ROOT/frontend/src/lib/"

echo "[5/6] Copying pages..."
cp "$SOURCE_ROOT/apps/homepage/frontend/src/pages/WorkflowManagerPage.tsx" \
   "$TARGET_ROOT/frontend/src/pages/"

# =============================================================================
# BACKEND: Services
# =============================================================================

echo "[6/6] Creating backend directory structure..."
mkdir -p "$TARGET_ROOT/backend/services"
mkdir -p "$TARGET_ROOT/backend/services/knowledge"

echo "[6a/6] Copying devtools service..."
cp "$SOURCE_ROOT/gateway/services/devtools_service.py" \
   "$TARGET_ROOT/backend/services/"

echo "[6b/6] Copying workflow service..."
cp "$SOURCE_ROOT/gateway/services/workflow_service.py" \
   "$TARGET_ROOT/backend/services/"

echo "[6c/6] Copying LLM service..."
cp "$SOURCE_ROOT/gateway/services/llm_service.py" \
   "$TARGET_ROOT/backend/services/"

echo "[6d/6] Copying knowledge/RAG services..."
cp -r "$SOURCE_ROOT/gateway/services/knowledge/"* \
      "$TARGET_ROOT/backend/services/knowledge/"

# =============================================================================
# CONTRACTS: Pydantic schemas
# =============================================================================

echo "[7/6] Creating contracts directory structure..."
mkdir -p "$TARGET_ROOT/contracts/devtools"

echo "[7a/6] Copying devtools contracts..."
cp "$SOURCE_ROOT/shared/contracts/devtools/api.py" \
   "$TARGET_ROOT/contracts/devtools/"

# Check if workflow.py exists
if [ -f "$SOURCE_ROOT/shared/contracts/devtools/workflow.py" ]; then
    cp "$SOURCE_ROOT/shared/contracts/devtools/workflow.py" \
       "$TARGET_ROOT/contracts/devtools/"
fi

# =============================================================================
# SUMMARY
# =============================================================================

echo ""
echo "=== Copy Complete ==="
echo ""
echo "Files copied:"
find "$TARGET_ROOT/frontend/src/components/workflow" -type f | wc -l | xargs echo "  - Workflow components:"
find "$TARGET_ROOT/frontend/src/hooks" -type f | wc -l | xargs echo "  - Hooks:"
find "$TARGET_ROOT/frontend/src/pages" -type f | wc -l | xargs echo "  - Pages:"
find "$TARGET_ROOT/backend/services" -type f | wc -l | xargs echo "  - Backend services:"
find "$TARGET_ROOT/contracts/devtools" -type f | wc -l | xargs echo "  - Contracts:"
echo ""
echo "Next steps:"
echo "  1. Run: cd frontend && npm install @monaco-editor/react @tanstack/react-query react-force-graph-2d react-force-graph-3d three @types/three"
echo "  2. Execute PLAN-0001 modification chunks (can run in parallel):"
echo "     - Track A (Frontend): Modify imports, API_BASE, routing"
echo "     - Track B (Backend): Modify imports, router mounts, contracts"
echo ""
echo "=== Done ==="
