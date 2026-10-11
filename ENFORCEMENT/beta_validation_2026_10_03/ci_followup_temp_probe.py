"""Diagnostic only: no repository imports, ACL edits, TEMP edits, or cleanup."""
import json, os, sys, tempfile, uuid
from pathlib import Path
base=Path(__file__).resolve().parent
results={"python":sys.version,"executable":sys.executable,"cases":[]}
for label,mode in [("mkdir_default",None),("mkdir_0700",0o700),("TemporaryDirectory",None)]:
    entry={"case":label}
    try:
        if label=="TemporaryDirectory":
            temporary=tempfile.TemporaryDirectory(prefix="ci_followup_",dir=base,delete=False)
            path=Path(temporary.name)
        else:
            path=base/("ci_followup_"+label+"_"+uuid.uuid4().hex[:8])
            if mode is None: os.mkdir(path)
            else: os.mkdir(path,mode)
        entry["path"]=str(path)
        entry["create"]="ok"
        for operation in ["write_read","mkdir_child","list"]:
            try:
                if operation=="write_read":
                    file=path/"probe.txt"
                    file.write_text("probe")
                    assert file.read_text()=="probe"
                elif operation=="mkdir_child": (path/"child").mkdir()
                else: list(path.iterdir())
                entry[operation]="ok"
            except OSError as error: entry[operation]={"type":type(error).__name__,"winerror":error.winerror,"errno":error.errno,"message":str(error)}
    except OSError as error: entry["create"]={"type":type(error).__name__,"message":str(error)}
    results["cases"].append(entry)
print(json.dumps(results,indent=2))
(base/"ci_followup_temp_probe.json").write_text(json.dumps(results,indent=2)+"\n")
