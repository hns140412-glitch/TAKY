---
name: netlify-router
description: Route Netlify work to the one relevant archived official skill; never load the whole Netlify skill set.
---
Official Netlify skill sources are preserved under `REFERENCE/CLAUDE_SKILLS/NETLIFY_OFFICIAL/`.
Load only the single task-relevant `SKILL.md` from that directory.

Routing hints:
- deploy / preview / branch deploy -> `netlify-deploy`
- build, redirects, headers, env -> `netlify-config`
- framework deploy -> `netlify-frameworks`
- serverless backend -> `netlify-functions`
- edge runtime -> `netlify-edge-functions`
- storage -> `netlify-blobs` or `netlify-database`
- auth -> `netlify-identity` or `netlify-access-control`
- forms / caching / image transforms -> matching skill
- custom MCP server -> `netlify-mcp-servers`

`netlify-ai-gateway` and `netlify-agent-runner` are HOLD by default under SAVEY because they can create redundant model usage or metered spend.
Production deploy remains a TAKY human-approval gate.
Do not load unrelated Netlify skills 'just in case'.
