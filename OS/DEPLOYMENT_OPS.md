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

## 3. VALIDATION
Validate required HTML/JS/CSS/manifest/service-worker/assets/paths/configuration as applicable.
Validation failure blocks Production apply.

## 4. REPORTING
Report separately:
- GitHub source update
- deployment-host result
- company-PC synchronization result

`GITHUB UPDATED ≠ DEPLOYED ≠ PC SYNCED`

## 5. CURRENT APP ALIAS
Use current product names.
Historical `ZPD Word` deployment aliases SHALL route to the current `Hide & Seek` product owner when the intended project is unambiguous.
