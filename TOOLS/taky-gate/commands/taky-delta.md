---
description: 오늘 수집된 편집·커밋·배포 기록으로 CURRENT DELTA 초안을 만든다
---
`python3 "${CLAUDE_PLUGIN_ROOT}/hooks/taky_delta.py" --draft` 를 실행하고 그 출력을 바탕으로 DELTA 한 단락을 쓴다.
실행 영수증이 없는 항목은 VERIFIED라고 쓰지 않는다. OPEN은 작성자가 채운다. CURRENT 문서에 쓰기 전에 USER에게 초안을 보여준다.
