"""RETIRED. The canonical architectural worktree already lives at TAKY_ARCHI GROW.
Never rewrite CURRENT authority or workspace from a legacy one-shot migration.
Original script: TAKY_AI_WORKBENCH/90_ARCHIVE/RETIRED_PATH_RENAME_SCRIPTS_20261013/archi_grow_update_references.py
"""
import json
from pathlib import Path
base=Path("D:/Git PWA")
current=base/"TAKY_ARCHI GROW"
old=base/"TAKY-WORK-OS"
authority=base/"TAKY"/"CURRENT"/"TAKY_PATH_AUTHORITY.md"
workspace=base/"TAKY_PROJECTS.code-workspace"
state="CURRENT_CANONICAL_PATH_PRESENT" if current.is_dir() else "CANONICAL_DIRECTORY_MISSING"
print(json.dumps({
 "schema":"TAKY_RETIRED_ARCHI_GROW_MIGRATION_GUARD_V1",
 "status":state,
 "canonical_directory":str(current),
 "retired_source_directory_present":old.exists(),
 "authority_present":authority.is_file(),
 "workspace_present":workspace.is_file(),
 "mutation_performed":False,
 "run_only":"AUDIT",
 "legacy_rewrite_disabled":True
},ensure_ascii=False))
raise SystemExit(0 if current.is_dir() and authority.is_file() else 2)
