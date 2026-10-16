"""Exercise offline TAKY review UI controls through actual local Chrome DOM.

Injects tests into an ephemeral copy, not into the production review console.
No external network, persistence, approvals, or deployed runtime.
"""
import html
import json
import re
import subprocess
import tempfile
from pathlib import Path

ORIGINAL=Path(r"D:\Git PWA\TAKY_AI_WORKBENCH\01_BACKLOG_AND_ADOPTION\80_EVIDENCE\TAKY_LOCAL_REVIEW_CONSOLE_875283c73ce17d400ac9.html")
CHROME=Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
CHECK=r"""
<script>
(async()=>{
 const r={};const $$=q=>document.querySelectorAll(q);
 const domain=document.querySelector('#domain');
 r.initial_sources=$$('#sourceList .source').length;
 domain.value='ARCHITECTURE';domain.dispatchEvent(new Event('change',{bubbles:true}));
 r.architecture_sources=$$('#sourceList .source').length;
 const search=document.querySelector('#search');
 search.value='건축';search.dispatchEvent(new Event('input',{bubbles:true}));
 r.search_result_count=$$('#sourceList .source').length;
 search.value='';search.dispatchEvent(new Event('input',{bubbles:true}));
 document.querySelector('#sourceList .source').click();
 const select=document.querySelector('#detail .review-row select');
 select.value='revisit';select.dispatchEvent(new Event('change',{bubbles:true}));
 const memo=document.querySelector('#detail textarea');
 memo.value='TECHNICAL_REVIEW_NOTE_ONLY';memo.dispatchEvent(new Event('input',{bubbles:true}));
 r.note_count=notes.size;
 r.note_status=[...notes.values()][0]?.status;
 let captured=null;
 URL.createObjectURL=blob=>{captured=blob;return 'blob:local-test'};
 URL.revokeObjectURL=()=>{};
 HTMLAnchorElement.prototype.click=function(){};
 document.querySelector('#exportNotes').click();
 if(!captured)throw Error('NO_REVIEW_EXPORT_BLOB');
 const data=JSON.parse(await captured.text());
 r.exported_notes=data.records.length;
 r.export_non_authoritative=data.non_authoritative;
 r.export_independent_approval=data.independent_approval;
 r.anchor_detail_count=$$('#detail .anchor').length;
 const file=new File([JSON.stringify(data)],'review-notes.json',{type:'application/json'});
 notes.clear();
 await document.querySelector('#importInput').onchange({target:{files:[file],value:''}});
 r.imported_notes=notes.size;
 r.imported_state=[...notes.values()][0]?.status;
 const output=document.createElement('pre');output.id='TAKY_TEST_RESULT';output.textContent=JSON.stringify(r);
 document.body.append(output);
})().catch(e=>{const output=document.createElement('pre');output.id='TAKY_TEST_ERROR';output.textContent=e.stack;document.body.append(output)});
</script>
"""


def check():
    markup=ORIGINAL.read_text(encoding="utf-8")
    if "independent_approval:false" not in markup:
        raise ValueError("APPROVAL_BOUNDARY_NOT_PRESENT_IN_CONSOLE")
    with tempfile.TemporaryDirectory(prefix="taky_ui_test_") as folder:
        folder=Path(folder)
        test=folder/"review-test.html"
        test.write_text(markup.replace("</body></html>",CHECK+"</body></html>"),
                        encoding="utf-8")
        result=subprocess.run([
            str(CHROME),"--headless=new","--no-sandbox","--disable-gpu",
            "--disable-extensions","--disable-background-networking",
            "--no-first-run","--no-default-browser-check",
            "--user-data-dir="+str(folder/"profile"),
            "--virtual-time-budget=3000","--dump-dom",test.as_uri()],
            text=True,encoding="utf-8",errors="replace",
            capture_output=True,timeout=28)
        if result.returncode:
            raise ValueError("CHROME_CLI_FAILED:"+result.stderr[-250:])
        if 'id="TAKY_TEST_ERROR"' in result.stdout:
            match=re.search(r'<pre id="TAKY_TEST_ERROR">(.*?)</pre>',
                            result.stdout,re.DOTALL)
            raise ValueError("BROWSER_UI_FUNCTION_ERROR:"+
                             html.unescape(match.group(1) if match else "UNKNOWN"))
        match=re.search(r'<pre id="TAKY_TEST_RESULT">(.*?)</pre>',
                        result.stdout,re.DOTALL)
        if not match:
            raise ValueError("BROWSER_DOM_INTERACTION_TEST_MISSING")
        values=json.loads(html.unescape(match.group(1)))
        if not (values["initial_sources"]==143 and
            values["architecture_sources"]==66 and values["search_result_count"]>0
            and values["note_count"]==1 and values["note_status"]=="revisit"
            and values["exported_notes"]==1
            and values["export_non_authoritative"] is True
            and values["export_independent_approval"] is False
            and values["anchor_detail_count"]>=1
            and values["imported_notes"]==1 and values["imported_state"]=="revisit"):
            raise ValueError("BROWSER_INTERACTION_ASSERTION_FAILED:"+repr(values))
        return values


if __name__=="__main__":
    print(json.dumps({"status":"REAL_CHROME_OFFLINE_REVIEW_INTERACTIONS_PASS",
                      **check()},ensure_ascii=False))
