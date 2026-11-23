# Local build v1.2 implementation plan

Goal: Telegram asks for software; local Windows agent creates source, installs project dependencies, runs actual build/tests and sends an artifact.
Spec: user approved Windows/WSL machine (RTX 5070). Implement Windows-native Python and Node build paths first; WSL detection only, Android APK and phone bridge not claimed.

Architecture: trusted build runner has fixed web/python/static profiles and uses subprocesses under a kill-on-close Windows job. Local setup explicitly enables generated-code execution once. This is NOT a sandbox. No deployment, arbitrary command expansion, or unrestricted source writes are enabled. Build feedback is passed to AI for bounded repair. Artifacts and verification stored per job. The actual output hash is checked after review so later edits cannot reuse stale build evidence.

Tasks:
- [x] Tests first: build failures cannot pass, missing outputs, cancellation, generated directories excluded from source and ZIP, successful Python tests, build evidence required for software finish.
- [x] Implement runner with dependency installs, bounded logs, timeout/cancel cleanup, per-project venv, static output and source digest.
- [x] Integrate build action and trusted completion gate; automatic result upload.
- [x] Add local preflight/setup BAT and Windows keep-awake guard while agent runs.
- [x] Pace Gemini requests and retry 429 respecting server delay; do not modify Telegram retry policy.
- [x] Test, fresh review, package with preserved config/state and truthful limitations.

Scope decisions: Node/npm must be installed locally; setup checks and explains missing dependencies. GPU is not used by Gemini API. Android phone pairing and APK build remain outstanding because SDK/phone-side components are not present. Long-running dev servers are not left running after tests.

Review: all 5 important findings fixed with regression tests. 45 tests pass. No minor findings deferred. Local host execution requires opt-in; Windows-specific live verification remains unavailable.
