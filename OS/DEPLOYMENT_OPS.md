# TAKY DEPLOYMENT OPS

Status: REV_00 / PRE-CONFIRMATION EVOLVING DESIGN SOURCE
Scope: governed PWA/web deployment workflow.

## 1. AUTHORITY
GitHub repository = central deployment source.
Netlify or equivalent linked host = deployment surface.
Company PC = synchronized local working copy, not canonical authority.

## 2. SAFE UPDATE
Before write/deploy, inspect current repository state and deployment configuration.

Classify files:
- PROTECTED: repository/deployment/local automation and other explicitly protected files
- MANAGED: app files intentionally managed by the deployment workflow

Only MANAGED files are automatically eligible for UPDATE/ADD.
Deletion is allowed only for a file that was previously managed and is intentionally absent from the new managed set.
Unknown pre-existing files SHALL NOT be automatically deleted.

A dirty/uncommitted company-PC state SHALL NOT be forcibly reset or overwritten without conflict handling.

## 3. DEPLOYMENT FILE NAMING — HARD LOCK

For governed PWA/web MASTER files, deployment ZIPs, validation reports and user-delivered deployment packages:
- no literal spaces in the actual filename;
- no `%` character;
- do not use URL-encoded `%20` as an official filename form;
- use `_` as the default word separator unless a project owner explicitly requires a stricter compatible rule.

`DISPLAY TITLE ≠ ACTUAL FILE NAME`
`URL ENCODING ≠ OFFICIAL FILE NAME`

Before packaging/release, validate the actual produced filenames rather than only the intended naming rule.

## 4. ILLUSTRATION / LIVE UI SEPARATION — HARD LOCK

Generated or approved illustration assets may own:
- world/environment/background;
- characters/companions;
- landmarks and decorative objects;
- material/texture/lighting/mood;
- non-functional visual props.

Functional and dynamic interface content SHALL remain live runtime UI where technically applicable:
- app/place names used as interface labels;
- questions and explanatory copy;
- buttons / CTA / tabs / navigation labels;
- progress, EXP/level/counters/dates/status;
- input fields, errors, accessibility text;
- user names, task state and other dynamic data.

Preferred realization:
`ILLUSTRATION ASSET + LIVE HTML/CSS/SVG/CANVAS UI + REAL DATA BINDING`

Hard distinctions:
`GENERATED TEXT IN IMAGE ≠ DEPLOYABLE LIVE UI`
`BACKGROUND ≠ UI`
`MOCKUP TEXT ≠ RUNTIME TEXT`

A generated image containing Korean/English text, numbers, buttons, progress, tabs or state indicators SHALL NOT be shipped as the functional UI merely because the mockup looks correct. Functional text baked into an image fails when it prevents reliable text integrity, responsive layout, accessibility, localization or dynamic state updates.

## 5. VALIDATION
Validate required HTML/JS/CSS/manifest/service-worker/assets/paths/configuration as applicable.
Validation failure blocks Production apply.

Deployment validation also checks, when applicable:
- actual filenames comply with the active naming contract;
- live text/buttons/status are not accidentally baked into background/mockup images;
- background/world imagery does not replace required interactive UI;
- generated-image text is not relied on as authoritative functional content.

## 6. REPORTING
Report separately:
- GitHub source update
- deployment-host result
- company-PC synchronization result

`GITHUB UPDATED ≠ DEPLOYED ≠ PC SYNCED`

## 7. CURRENT APP ALIAS
Use current product names.
Superseded former-name deployment aliases SHALL route to the current `Hide & Seek` product owner when the intended project is unambiguous.
