"""Validate every locally generated Korean TTS WAV and its approved-source mapping."""
import array, hashlib, json, wave
from pathlib import Path
root=Path(r"D:\Git PWA\TAKY\staging\crew_voice_20261012\mock_tts")
manifest=json.loads((root/"EXPLORER_CREW_TTS_MOCK_MANIFEST_264.json").read_text(encoding="utf-8-sig"))
rows=manifest["clips"]
problems=[]
durations=[]
rates=set()
group_counts={}
total_bytes=0
for row in rows:
    key=row["key"]; target=root/row["relative_path"]
    try:
        raw=target.read_bytes()
        total_bytes+=len(raw)
        if hashlib.sha256(raw).hexdigest()!=row["wav_sha256"]:
            raise ValueError("hash mismatch")
        with wave.open(str(target),"rb") as w:
            rate=w.getframerate();frames=w.getnframes();ch=w.getnchannels();width=w.getsampwidth()
            if ch!=1 or width!=2 or w.getcomptype()!="NONE": raise ValueError("unsupported audio format")
            secs=frames/rate
            if secs<.3 or secs>40: raise ValueError("invalid duration")
            audio=array.array('h',w.readframes(frames))
            if max(abs(v) for v in audio[::max(1,len(audio)//1024)])<150:
                raise ValueError("sampled audio silent")
            durations.append(secs);rates.add(rate)
            group_counts[row["voice_family"]]=group_counts.get(row["voice_family"],0)+1
    except Exception as e:
        problems.append({"key":key,"error":str(e)})
report={"status":"PASS" if not problems and len(rows)==264 else "FAIL","clip_count":len(rows),
        "voice_groups":group_counts,"sample_rates":sorted(rates),
        "total_bytes":total_bytes,"duration_min_sec":round(min(durations),2) if durations else None,
        "duration_max_sec":round(max(durations),2) if durations else None,
        "total_duration_sec":round(sum(durations),1),"issues":problems}
(root/"WAV_DECODE_QA.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report,ensure_ascii=False))
raise SystemExit(0 if report["status"]=="PASS" else 2)
