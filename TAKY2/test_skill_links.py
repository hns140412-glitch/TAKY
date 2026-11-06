#!/usr/bin/env python3
"""Disposable fixture for TAKY2 skill-links migration; no edits to user repos."""
from __future__ import annotations
import contextlib,importlib.util,io,json,pathlib,shutil,tempfile
SCRIPT=pathlib.Path(__file__).with_name("skill_links.py")
spec=importlib.util.spec_from_file_location("skill_links",SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
manifest=mod.get_manifest()
actual=mod.canonical_source(mod.HERE)  # works for the real TAKY/.local/TAKY-2.0-ORCH layout

def states(target):
    return [r[-1] for r in mod.collect(target)]
def snapshot(root):
    return mod.tree_digest(root)
def make_fixture(parent,nested):
    source=parent/"TAKY"
    target=(source/".local" if nested else parent)/"TAKY-2.0-ORCH"
    (source/".git").mkdir(parents=True)
    (target/".git").mkdir(parents=True)
    for skill in manifest["skills"]:
        shutil.copytree(actual/".claude"/"skills"/skill,source/".claude"/"skills"/skill)
    return source,target
def run_check(target):
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf):
        code=mod.main(["check","--repo",str(target)])
    return code,json.loads(buf.getvalue())
def materialize(source,target):
    for consumer in mod.CONSUMERS:
        for skill in manifest["skills"]:
            shutil.copytree(source/".claude"/"skills"/skill,target/consumer/skill)

for nested in (False,True):
    label="nested" if nested else "sibling"
    with tempfile.TemporaryDirectory(prefix="TAKY2_SKILLS_PORTABILITY_") as d:
        source,target=make_fixture(pathlib.Path(d),nested)
        assert mod.canonical_source(target)==source.resolve(),label
        assert len(mod.collect(target))==22
        assert all(s=="MISSING" for s in states(target))
        created=mod.restore(target)
        assert len(created)==22,len(created)
        assert all(s=="LINK_VALID" for s in states(target))
        assert mod.restore(target)==[], "IDEMPOTENCY_BROKEN"
        code,out=run_check(target)
        assert code==0 and out["status"]=="PASS" and out["valid_links"]==22 and out["verified_content_dirs"]==0,out
        # A failed source hash must never modify any existing link.
        victim=source/".claude"/"skills"/"authority-check"/"SKILL.md"
        original=victim.read_bytes()
        victim.write_bytes(original+b"\nUNAPPROVED_MUTATION")
        try:
            mod.restore(target)
            raise AssertionError("TAMPERED_SOURCE_ACCEPTED")
        except RuntimeError as err:
            assert "SOURCE_HASH_DRIFT" in str(err)
        victim.write_bytes(original)

with tempfile.TemporaryDirectory(prefix="TAKY2_SKILLS_PORTABILITY_") as d:
    source,target=make_fixture(pathlib.Path(d),True)
    materialize(source,target)
    assert all(s=="VERIFIED_CONTENT" for s in states(target))
    assert mod.restore(target)==[]
    code,out=run_check(target)
    assert code==0 and out["status"]=="PASS" and out["valid_links"]==0 \
        and out["verified_content_dirs"]==22 and out["valid_consumers"]==22,out
    assert out["model_invoked"] is False
    src_before=snapshot(source/".claude")
    skill="authority-check"
    cases={
        "tampered":lambda p:(p/"SKILL.md").write_bytes((p/"SKILL.md").read_bytes()+b"\nX"),
        "extra":lambda p:(p/"extra.txt").write_text("unexpected"),
        "missing":lambda p:(p/"SKILL.md").unlink(),
        "extra_dir":lambda p:(p/"emptydir").mkdir(),
    }
    for name,mutate in cases.items():
        victim=target/".agents"/"skills"/skill
        backup=snapshot(victim)
        mutate(victim)
        assert states(target).count("DESTINATION_OCCUPIED")==1,name
        mutated=snapshot(victim)
        try:
            mod.restore(target)
            raise AssertionError("CONFLICT_ACCEPTED:"+name)
        except RuntimeError as err:
            assert "DESTINATION_CONFLICT" in str(err),name
        assert snapshot(victim)==mutated,"CONFLICT_MUTATED:"+name  # no mutation
        code=None
        try:
            run_check(target)
        except RuntimeError as err:
            assert "UNSAFE_LINK_CONFLICT" in str(err)
        shutil.rmtree(victim)
        shutil.copytree(source/".claude"/"skills"/skill,victim)
        assert snapshot(victim)==backup
    assert all(s=="VERIFIED_CONTENT" for s in states(target))
    # A link descendant inside a materialized dir is a conflict, not verified content.
    victim=target/".claude"/"skills"/skill
    try:
        (victim/"alias").symlink_to(victim/"SKILL.md")
    except OSError:
        pass  # symlink privilege unavailable; covered by tree_digest on platforms that allow it
    else:
        assert states(target).count("DESTINATION_OCCUPIED")==1
        (victim/"alias").unlink()
    # Mixed: missing consumers get links while verified dirs stay untouched.
    shutil.rmtree(target/".claude"/"skills"/"handoff")
    assert len(mod.restore(target))==1
    code,out=run_check(target)
    assert code==0 and out["valid_links"]==1 and out["verified_content_dirs"]==21,out
    assert snapshot(source/".claude")==src_before  # source never mutated

print("SKILL_RESTORE_FIXTURE_PASS: sibling+nested layouts, links22, verified_content22, "
      "tamper/extra/missing-HOLD, source-drift-HOLD, idempotent, no_mutation")
