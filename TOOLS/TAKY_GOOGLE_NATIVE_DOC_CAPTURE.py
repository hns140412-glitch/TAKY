"""One native Google Doc text-export intake; original Drive Doc remains untouched."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(r"D:\Git PWA\TAKY\TOOLS")))
from TAKY_GOOGLE_DRIVE_RAW_INTAKE import original
item={"account":"HNS","drive_id":"1zVU2Yf9mGEDPRmLFXApUn4NOjhtoHWjhbnQXjGLFyS0",
 "file_name":"DATA_MINING_ENGINE_CURRENT_2026-09-24.txt","bytes":27947,
 "category":"30_AI_TECH","native_export":True}
report=original(item)
if report["size_bytes"]!=item["bytes"] or "EXPORT" not in report["state"]:
 raise RuntimeError("NATIVE_DOC_EXPORT_BAD_STATE")
receipt=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\REFERENCE\99_CONTROL\HNS_NATIVE_DOC_EXPORT_20261013.json")
receipt.write_text(json.dumps({"schema":"TAKY_DRIVE_NATIVE_DOC_EXPORT_CAPTURE_V1",
 "native_source_id":item["drive_id"],"export_mime":"text/plain",
 "native_original_remains_in_google_drive":True,"snapshot":report,
 "authority":"DERIVED_TEXT_EXPORT_NOT_FULL_NATIVE_DOC_RAW"},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"status":report["state"],"size_bytes":report["size_bytes"],"source_id":report["source_id"]},ensure_ascii=False))
