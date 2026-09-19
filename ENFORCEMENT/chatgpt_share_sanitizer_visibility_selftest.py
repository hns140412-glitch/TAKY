#!/usr/bin/env python3
from chatgpt_share_transcript_sanitizer import extract_messages

data={
 "linear_conversation":[
  {"id":"u1","message":{"author":{"role":"user"},"create_time":1,"content":{"content_type":"text","parts":["visible user"]}}},
  {"id":"a-internal-1","message":{"author":{"role":"assistant"},"create_time":2,"content":{"content_type":"thoughts","parts":["PRIVATE INTERNAL"]}}},
  {"id":"a-internal-2","message":{"author":{"role":"assistant"},"create_time":3,"content":{"content_type":"reasoning_recap","parts":["PRIVATE INTERNAL"]}}},
  {"id":"a-internal-3","message":{"author":{"role":"assistant"},"create_time":4,"content":{"content_type":"model_editable_context","parts":["PRIVATE INTERNAL"]}}},
  {"id":"a-internal-4","message":{"author":{"role":"assistant"},"create_time":5,"content":{"content_type":"code","parts":["PRIVATE INTERNAL"]}}},
  {"id":"a1","message":{"author":{"role":"assistant"},"create_time":6,"content":{"content_type":"text","parts":["visible assistant"]}}},
  {"id":"u2","message":{"author":{"role":"user"},"create_time":7,"content":{"content_type":"multimodal_text","parts":["visible multimodal",{"content_type":"image_asset_pointer"}]}}}
 ]
}
messages,counters=extract_messages(data)
assert [m["text"] for m in messages][:2]==["visible user","visible assistant"]
assert len(messages)==3, messages
joined="\n".join(m["text"] for m in messages)
assert "PRIVATE INTERNAL" not in joined
assert counters["excluded_non_user_assistant"]==4, counters
assert counters["non_text_parts"]==1, counters
print("PASS: visible-message-only sanitizer selftest")
