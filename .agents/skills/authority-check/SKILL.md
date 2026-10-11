---
name: authority-check
description: Resolve TAKY authority before making a material decision or edit.
---
Identify the user-visible goal and namespace.
Resolve: user instruction -> canonical owner -> live state -> task contract -> recovery evidence.
Classify sources as ACTIVE / REFERENCE_ONLY / CANDIDATE / HOLD / SUPERSEDED.
If two active owners conflict, stop the conflicting change and report exact evidence.
Do not let HANDOFF, memory, or old SHA silently override current authority.
