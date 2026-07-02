# AGENTS.md

# Alchemist Development Guidelines

## Project Mission

Alchemist is a cross-platform audiobook workflow application for metadata management, duplicate detection, conversion, and Audiobookshelf library operations.

It is **not** simply a metadata editor.

Every feature should support one or more of the following goals:

- Improve metadata quality.
- Reduce repetitive user work.
- Protect the user's audiobook library.
- Make operations transparent and explainable.
- Remain maintainable for many years.

When making implementation decisions, prefer safety, clarity, and maintainability over cleverness.

Alchemist is intended to be software that its author is proud to maintain five years from now. Every implementation decision should optimize for long-term clarity, correctness, and maintainability over short-term convenience.

---

# Governing Documentation

Implementation work must remain consistent with:

- `docs/adr/`
- `docs/architecture/1000-system-architecture/1000-system-architecture.md`
- relevant subsystem specifications under `docs/architecture/`

When documentation conflicts, prefer the accepted ADRs and raise the conflict rather than guessing.

---

# Architectural Philosophy

This project follows a layered architecture.

```text
UI
 ↓
Commands
 ↓
Execution Plans
 ↓
Services
 ↓
Persistence / External Systems
```

The UI is responsible only for presentation and user interaction.

Commands translate user intent into Execution Plans.

Execution Plans are the executable artifacts.

Services implement focused business capabilities.

Operation Records preserve the history of executed plans.

---

# Core Principles

## Files are the source of truth.

SQLite exists to store:

- settings
- scan cache
- metadata history
- operation history
- indexes

Never assume SQLite is authoritative over the user's files.

---

## Never modify metadata automatically.

Metadata may only be written when the user performs an explicit Save or Execute operation.

Background scans must never modify files.

---

## Planning always precedes execution.

Significant operations must support:

- validation
- Execution Plan generation
- approval when required
- plan execution
- Operation Record creation

Do not perform destructive operations directly from UI events.

Do not execute a materially different plan than the user approved.

---

## Recoverability is preferred over speed.

Whenever practical:

- Archive first.
- Validate.
- Execute.
- Verify.
- Record what happened.

Never delete data simply because it is convenient.

---

## Explainability matters.

If Alchemist performs an operation, the user should be able to understand:

- why
- what
- how

Execution Plans are first-class architectural objects.

Operation Records should explain what actually happened.

---

# Layer Responsibilities

## UI

Responsible for:

- widgets
- dialogs
- presentation
- progress
- user interaction
- plan display
- Decision Gate interaction

Must NOT:

- read/write metadata
- call ffmpeg
- call ABS directly
- perform duplicate detection
- execute filesystem operations
- orchestrate service workflows directly

---

## Commands

Commands generate Execution Plans.

Examples:

- `SaveMetadataCommand`
- `ConvertBookCommand`
- `ReplaceLibraryItemCommand`
- `CheckDuplicatesCommand`

Every command should support:

- `validate_inputs()`
- `gather_context()`
- `build_execution_plan()`
- `return_plan_or_errors()`

Commands must not directly execute workflow steps.

---

## Execution Plans

Execution Plans describe proposed work before it happens.

Plans should describe:

- purpose
- inputs
- expected outputs
- steps
- warnings
- risks
- approval requirements
- recovery options

Approved plans are immutable.

If the environment changes in a way that affects the outcome, invalidate the plan and rebuild it.

---

## Services

Services implement business logic.

Examples:

- `Scanner`
- `MetadataService`
- `FFmpegManager`
- `ABSManager`
- `PlacementEngine`

Services should not know about Qt widgets.

---

## Persistence

SQLite stores:

- settings
- cache
- history
- indexes

Never store cover-art blobs.

---

# Metadata

Use canonical metadata internally.

Never expose tag implementation details to higher layers.

Aliases are configurable.

Canonical names are not configurable.

Canonical metadata is divided into:

- Canonical Business Metadata (CBM)
- Canonical Technical Metadata (CTM)
- Canonical Application Metadata (CAM)

Resolved canonical values should preserve provenance whenever practical.

---

# Identity

Books have `ALCHEMIST_ID` values.

Multi-track books have `ALCHEMIST_TRACK_ID` values for each track.

Application identifiers are assigned internally on discovery but are embedded only during explicit user-approved metadata writes.

ASIN, ISBN, filenames, folder names, and paths are matching signals, not primary identity.

---

# Scanning

Scanning must be incremental.

Never rescan the entire library after routine edits.

Use cache invalidation.

Prefer updating a single book over rebuilding everything.

Scanning must not write metadata to user files.

---

# Performance

Avoid unnecessary filesystem access.

Avoid repeated ffprobe calls.

Avoid repeated mutagen reads.

Every expensive operation should have a cache and a clear invalidation strategy.

---

# Coding Standards

Python 3.12

Type hints are expected.

Prefer dataclasses for models.

Prefer enums over string constants.

Prefer composition over inheritance.

Avoid global state.

Avoid singleton patterns.

Small functions are preferred.

---

# Error Handling

Never silently ignore exceptions.

Surface actionable errors.

Operations should fail gracefully.

Whenever possible, leave user data untouched.

---

# Logging

Every significant operation should create an Operation Record.

Important events should be logged.

Logs should explain:

- what happened
- why
- duration
- result

Operation Records are the historical records of executed plans, not just text logs.

---

# User Experience

Prefer confirmation over surprise.

Prefer information over assumptions.

Users should understand what the software is doing.

Friction should be intentional and functional.

---

# Documentation

New architectural decisions should include an ADR.

New features should include:

- specification
- implementation
- acceptance criteria

Keep documentation current.

---

# Things We Intentionally Do NOT Do

No automatic metadata writes.

No direct Audiobookshelf database modifications.

No silent destructive operations.

No rescanning the entire library after every change.

No cover art blobs in SQLite.

No UI directly calling FFmpeg.

No UI directly calling ABS.

No mutable natural keys.

No commands directly executing workflows.

---

# Lessons Learned

FletchAudio demonstrated that:

- UI responsiveness must never depend on filesystem scans.
- Metadata should be canonicalized.
- Execution Plans reduce mistakes.
- Incremental scanning scales.
- Architecture should be designed before implementation.
- Users should not be forced outside the application for normal audiobook workflows.

---

# When Unsure

When multiple reasonable implementations exist, choose the one that:

1. Preserves architecture.
2. Is easier to understand.
3. Is easier to test.
4. Is safer for user data.
5. Is easier to extend in the future.

Code is temporary.

Architecture is long-lived.

---

# Coding Philosophy

1. Prefer obvious code over clever code.
2. If you touch a module and can make a small improvement without expanding scope, do so.

Examples:

- Better type hints
- Clearer variable names
- Remove dead code
- Improve docstring
- Add a missing test unit

---

# Bug Fixing

1. Do not patch around bugs.
2. Identify the architectural cause whenever possible.
3. If a workaround is necessary, document why.
