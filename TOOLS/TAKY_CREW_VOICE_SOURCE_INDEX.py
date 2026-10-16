"""One derived index for 264 approved-script keys vs mock-only assets.
No recording, deployment, generated media, source mutation or approval promotion.
"""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(r"D:/Git PWA")
SOURCE=ROOT/"TAKY"/"staging"/"crew_voice_20261012"
OUT=ROOT/"TAKY_AI_WORKBENCH"/"00_CONTROL"/"TAKY_CREW_VOICE_SOURCE_INDEX.json"
LEDGER=SOURCE/"EXPLORER_CREW_PRODUCER_LINE_LEDGER_20261013.json"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for block in iter(lambda:f.read(262144),b""):h.update(block)
 return h.hexdigest()
def build():
 ledger=json.loads(LEDGER.read_text(encoding="utf-8-sig"))
 rows=ledger["rows"]
 if len(rows)!=264:raise ValueError("LOCKED_SOURCE_LINE_COUNT_DRIFT")
 refs=[];seen=set()
 for row in rows:
  key=row["script_key"]
  if key in seen:raise ValueError("DUPLICATE_SOURCE_SCRIPT_KEY:"+key)
  seen.add(key)
  phrase=row["text_exact"]
  text_hash=hashlib.sha256(phrase.encode("utf-8")).hexdigest()
  if text_hash!=row["text_sha256"]:raise ValueError("LOCKED_DIALOGUE_HASH_MISMATCH:"+key)
  wav=SOURCE/"mock_tts"/row["mock_audio_file"]
  if not wav.is_file():raise FileNotFoundError("MISSING_MOCK_AUDIO:"+key)
  if not wav.resolve().is_relative_to((SOURCE/"mock_tts").resolve()):
   raise ValueError("MOCK_PATH_ESCAPES_SOURCE_ROOT:"+key)
  # Candidate source may contain an expected future MP3 path. This path is
  # never interpreted as approval or permission to record.
  refs.append({
   "script_key":key,
   "character_id":row["character_id"],
   "scope":row["scope"],
   "voice_family":row["voice_family"],
   "locked_text_sha256":text_hash,
   "original_ledger_ref":str(LEDGER),
   "mock_wav_ref":str(wav),
   "mock_wav_sha256":sha(wav),
   "mock_asset_status":"TTS_MOCK_ONLY",
   "expected_approved_mp3_ref":row.get("original_audio_file"),
   "approved_mp3_ref":None,
   "approval_state":"NOT_RECORDING_APPROVED",
   "runtime_replacement_state":"MOCK_AUDIO_ONLY"
  })
 actual_wavs={str(p.resolve()) for p in SOURCE.rglob("*.wav")}
 referenced={str(Path(x["mock_wav_ref"]).resolve()) for x in refs}
 if actual_wavs!=referenced:raise ValueError("UNMAPPED_OR_MISSING_MOCK_AUDIO")
 approved_files=[x for x in SOURCE.rglob("*.mp3") if x.is_file()]
 if approved_files:raise ValueError("MP3_FILES_PRESENT_REQUIRE_SEPARATE_APPROVAL_REVIEW")
 return {
  "schema":"TAKY_CREW_VOICE_SOURCE_LOCATION_INDEX_V1",
  "authority":"APPROVED_SCRIPT_TEXT_LOCK_NOT_RECORDING_APPROVAL",
  "source_root":str(SOURCE),"ledger_sha256":sha(LEDGER),
  "script_count":len(refs),"wav_count":len(actual_wavs),
  "voice_group_count":len({x["voice_family"] for x in refs}),
  "real_recording_count_under_source_root":0,
  "recording_release_approved":False,
  "voice_records":refs,
  "raw_audio_moved":False,
  "paid_api_called":False
 }
def main():
 parser=argparse.ArgumentParser()
 group=parser.add_mutually_exclusive_group(required=True)
 group.add_argument("--build",action="store_true")
 group.add_argument("--check",action="store_true")
 args=parser.parse_args()
 doc=build()
 if args.build:
  OUT.parent.mkdir(parents=True,exist_ok=True)
  tmp=OUT.with_suffix(".json.tmp")
  tmp.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  tmp.replace(OUT)
 else:
  if not OUT.is_file() or json.loads(OUT.read_text(encoding="utf-8-sig"))!=doc:
   raise SystemExit("VOICE_SOURCE_OR_REFERENCE_DRIFT")
 print(json.dumps({"status":"PASS","script_count":doc["script_count"],
   "wav_count":doc["wav_count"],"voice_groups":doc["voice_group_count"],
   "approved_mp3_under_source_root":0,
   "derived_index":str(OUT),"voice_recording_started":False},ensure_ascii=False))
 return 0
if __name__=="__main__":sys.exit(main())
