# Saved ChatGPT Share HTML Sanitization

Purpose: convert saved ChatGPT share-page HTML into NotebookLM-safe, transcript-only Markdown without copying session/bootstrap/application data.

Flow:
`SAVED SHARE HTML -> React Router loader decode -> linear_conversation -> USER/ASSISTANT only -> explicit non-text markers -> security scan -> transcript validator -> NotebookLM source registry`.

Commands:
```bash
python ENFORCEMENT/chatgpt_share_transcript_sanitizer.py source.html -o sanitized.md
python ENFORCEMENT/chatgpt_share_transcript_validator.py sanitized.md
```

Hard boundaries:
- original HTML remains evidence and is not a NotebookLM input;
- sanitized output is a DERIVED transcript, not the original file;
- non-text parts are marked, not silently represented as recovered text;
- account-history completeness is not inferred from one saved share page;
- any failed security scan keeps the source in SECURITY_HOLD / SANITIZE_REQUIRED.
