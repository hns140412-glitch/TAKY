#!/usr/bin/env python3
"""Synthetic negative and positive regression for staged source coordinate claims."""
import copy
from data_index_detail_contract import SCHEMA, validate_detail_candidate
BASE={"schema":SCHEMA,"source_id":"teacher-1","original_locator":"https://drive.google.com/file/d/teacher-1/view",
      "coverage":"PARTIAL_REVIEWED_UNIT","observed_at":"2026-09-29","extract_recipe":"PYMUPDF_TEXT_AND_RENDER_V1",
      "evidence_note":"Visible heading confirmed","modality":"PDF",
      "inspection_methods":["PDF_TEXT_EXTRACT","RENDERED_PAGE_VISUAL"],
      "coordinate":{"physical_page_1based":9,"pdf_index_0based":8,"document_page_count":67,
                    "printed_page_label":"3","section_heading":"교과 및 성취기준 정보"}}
def reject(change, message):
    test=copy.deepcopy(BASE);change(test)
    try: validate_detail_candidate(test)
    except ValueError as e: assert message in str(e), (message,str(e))
    else: raise AssertionError("accepted invalid coordinate "+message)
doc=validate_detail_candidate(BASE)
assert doc["coordinate"]["pdf_index_0based"]==8 and doc["complete_source_review"] is False
assert doc["current_promoted"] is False and doc["state"]=="DETAIL_CANDIDATE_REVIEWED_NOT_CURRENT"
reject(lambda r:r["coordinate"].update(pdf_index_0based=9),"PDF_PAGE_INDEX_MISMATCH")
reject(lambda r:r["coordinate"].update(document_page_count=8),"PDF_PAGE_INDEX_MISMATCH")
reject(lambda r:r["coordinate"].update(section_heading=""),"SECTION_HEADING_REQUIRED")
reject(lambda r:r.update(coverage="COMPLETE_REVIEWED"),"COVERAGE_OVERCLAIM")
reject(lambda r:r.update(inspection_methods=["PDF_TEXT_EXTRACT"]),"VISUAL_METHOD_REQUIRED")
reject(lambda r:r.update(original_locator="file:///tmp/file.pdf"),"LOCATOR_INVALID")
img={**BASE,"modality":"IMAGE","source_id":"img-1","inspection_methods":["ORIGINAL_IMAGE_VISUAL"],
     "extract_recipe":"ORIGINAL_IMAGE_DIMENSIONS_AND_VISUAL_V1",
     "coordinate":{"width_px":1206,"height_px":2622,"pixel_region":[0,0,1206,2622],"carousel_slide":1}}
assert validate_detail_candidate(img)["modality"]=="IMAGE"
for region in ([0,0,1207,2622],[-1,0,300,300],[0,0,0,40]):
    bad=copy.deepcopy(img);bad["coordinate"]["pixel_region"]=region
    try: validate_detail_candidate(bad)
    except ValueError as e: assert "PIXEL_REGION" in str(e)
    else: raise AssertionError("out-of-bounds region passed")
video={**BASE,"modality":"VIDEO","source_id":"video-1","inspection_methods":["DECODED_FRAME_VISUAL"],
       "extract_recipe":"FFPROBE_DURATION_FFMPEG_FRAME_V1",
       "coordinate":{"duration_seconds":0.458186,"timestamp_seconds":0.05,
                     "frame_width_px":1206,"frame_height_px":2622}}
assert validate_detail_candidate(video)["coordinate"]["timestamp_seconds"]==0.05
for t in [-0.01,0.458186,float("nan"),float("inf"),True]:
    bad=copy.deepcopy(video);bad["coordinate"]["timestamp_seconds"]=t
    try:validate_detail_candidate(bad)
    except ValueError as e:assert "VIDEO_TIME" in str(e)
    else:raise AssertionError("invalid video time passed")
print("data_index_detail_contract: PASS (PDF page/printed distinction; image geometry; video time; negative gates)")
