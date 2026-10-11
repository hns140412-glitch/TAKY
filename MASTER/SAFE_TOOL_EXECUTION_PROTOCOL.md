# SAFE TOOL EXECUTION PROTOCOL

Status: ACTIVE
Rule ID: TKY-SAFEEXEC-001
Owner: MASTER/SAFE_TOOL_EXECUTION_PROTOCOL.md

## Purpose

Prevent avoidable tool/safety blocks and repeated execution mistakes before a command is sent.

## Non-negotiable execution rules

1. EXACT TARGET FIRST
   - Use a known repo path, file path, Drive file ID, or Drive folder ID.
   - Do not search an entire drive or system area when a narrower authority target exists.

2. CONNECTOR BEFORE LOCAL REVERSE-ENGINEERING
   - Google Drive work uses Drive file/folder IDs and the Drive connector first.
   - Local DriveFS paths are optional mirrors, never a prerequisite when the remote Drive source is authoritative.
   - Do not infer account identity from drive letters, volume labels, or unrelated local folders.

3. AUTH/ACCOUNT-ADJACENT ENUMERATION IS NOT A DISCOVERY ROUTE
   - Do not broadly enumerate credential, token, profile, browser-auth, or account cache areas merely to locate a resource.
   - Examples requiring explicit necessity: AppData account caches, DriveFS profile internals, credential stores, .ssh, token stores, broad environment-variable dumps.

4. ONE CALL, ONE PRIMARY PURPOSE
   - Do not bundle unrelated inspection, mutation, validation, cleanup, and deployment into one shell command.
   - Split multi-step work at evidence boundaries.

5. NO BLIND RETRY AFTER SAFETY BLOCK
   - A blocked command signature must not be resubmitted unchanged or with cosmetic edits.
   - Re-plan using a narrower target, dedicated connector, or direct file tool.

6. FILE TOOLS BEFORE SHELL FOR FILE I/O
   - Prefer read_file/write_file/search for known files and scoped searches.
   - Use shell only when computation, tests, or program execution is the actual task.

7. USER != DEBUGGER
   - Do not ask the user to diagnose tool-routing mistakes that can be resolved from existing authority data.
   - Fail closed only when a real external authorization or human decision is required.

## Google Drive reference intake

Primary ingress:
Google Drive folder ID -> remote inventory -> source materialization/hash -> intake contract -> Mining.

Local DriveFS:
OPTIONAL MIRROR ONLY.

## Acceptance

A tool action is executable only when the SAFE TOOL ACTION GATE returns PASS.
A blocked action must return concrete reasons and a safer route.
