# Agentlar Telegram v1

User intent: a first Windows version of a Telegram-controlled AI team which proposes and begins work, creates software, and reads explicitly selected personal data.

Selected approach: a local Python service, Telegram long polling and Gemini REST API. No inbound port, no hosting account. Alternatives: hosted service lacks local data; desktop GUI adds work without improving Telegram operation. User chose first local version and asked to proceed.

Roles: planner, builder and reviewer are separate prompts on a configurable Gemini model, not separate trained models. One active job; persisted history, cancellation, resume and bounded API requests. Text tools list/read/write files, read allowlisted text sources, syntax-check Python/JSON, and request an explicitly approved host command. Output ZIP sent to owner. No automatic deployment or arbitrary browser/phone access.

Constraints: Python 3.11+, standard library only; owner ID and private-chat enforcement before AI or file access; secrets in local config never available to model; writes only inside job directory; model is not trusted to enforce permissions; file size 256 KiB, 200 generated files, 5 MiB total generated source, max 24 builder steps per run. Host commands off by default and never run without exact command approval. Read source data may be sent to Google; disclose at setup.

Acceptance: offline tests verify traversal, symlink and Windows path rejection, authorization, persistence, cancellation, approvals, malformed model output and end-to-end mocked API generation. Live Telegram/Gemini and Windows launch remain unverified without user's credentials/device. V1 does not promise fully verified arbitrary software.
