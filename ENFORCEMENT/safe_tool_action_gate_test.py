from ENFORCEMENT.safe_tool_action_gate import evaluate

def test_exact_drive_connector_passes():
    r=evaluate({
      "operation":"google_drive",
      "purpose":"read canonical inbox",
      "target":"folder_id:1upSxxdECT5MCC1fvPJFOi24kk7K0LoOB",
      "transport":"connector",
      "connector_available":True,
      "drive_folder_id":"1upSxxdECT5MCC1fvPJFOi24kk7K0LoOB",
      "action_signature":"drive-folder-read-v1",
    })
    assert r["pass"] is True

def test_drivefs_reverse_lookup_blocked_when_connector_exists():
    r=evaluate({
      "operation":"google_drive",
      "purpose":"find inbox",
      "target":r"C:\\Users\\x\\AppData\\Local\\Google\\DriveFS",
      "transport":"drivefs_reverse_lookup",
      "connector_available":True,
      "drive_folder_id":"1upSxxdECT5MCC1fvPJFOi24kk7K0LoOB",
      "action_signature":"drivefs-profile-enum",
    })
    assert r["pass"] is False
    assert "DRIVE_CONNECTOR_ID_ROUTE_REQUIRED" in r["detected"]

def test_broad_env_dump_blocked():
    r=evaluate({
      "operation":"shell",
      "purpose":"find setting",
      "target":"known repo",
      "transport":"shell",
      "command":"Get-ChildItem Env:",
      "action_signature":"env-dump",
    })
    assert "BROAD_ENV_ENUMERATION_FORBIDDEN" in r["detected"]

def test_same_blocked_signature_cannot_retry():
    r=evaluate({
      "operation":"shell",
      "purpose":"retry",
      "target":"known target",
      "transport":"shell",
      "previous_block_signature":"abc",
      "action_signature":"abc",
    })
    assert "BLOCKED_ACTION_SIGNATURE_RETRY_FORBIDDEN" in r["detected"]

def test_file_io_prefers_file_tool():
    r=evaluate({
      "operation":"file",
      "purpose":"read file",
      "target":r"D:\\Git PWA\\TAKY\\MASTER\\RULE_REGISTRY.json",
      "transport":"shell",
      "file_io_only":True,
      "action_signature":"shell-cat-file",
    })
    assert "FILE_TOOL_REQUIRED_BEFORE_SHELL" in r["detected"]
