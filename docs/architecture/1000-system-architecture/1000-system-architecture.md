# 1000 - System Architecture Specification

## Document Control

| Field | Value |
|---|---|
| Project | Alchemist |
| Document | 1000 - System Architecture Specification |
| Status | Draft |
| Target Audience | Project owner, contributors, AI coding agents |
| Purpose | Define the technical architecture that all subsystem specifications and implementation work must follow. |

---

# 1. Purpose

This specification defines the system-level architecture for Alchemist.

Alchemist is a cross-platform desktop application for audiobook metadata management, duplicate detection, conversion, and Audiobookshelf library operations.

This document is not a feature specification. It defines the architectural boundaries, responsibilities, dependency rules, and system patterns that future subsystem specifications must follow.

---

# 2. Architectural Goals

Alchemist must be:

- **Safe** — user data must be protected by default.
- **Explainable** — significant actions must be planned and described before execution.
- **Recoverable** — destructive operations should be reversible whenever practical.
- **Incremental** — expensive operations should avoid unnecessary repeated work.
- **Maintainable** — responsibilities should be separated cleanly.
- **Testable** — core logic must be testable without a GUI.
- **Cross-platform** — Windows, Linux, and macOS must be supported.
- **Extensible** — future features should be added through well-defined seams.

---

# 3. Core Architecture

Alchemist follows a layered architecture.

```text
UI Layer
   ↓
Command Layer
   ↓
Service Layer
   ↓
Persistence / External Systems
```

The direction of dependency is downward only.

Higher layers may depend on lower layers.

Lower layers must not depend on higher layers.

---

# 4. Layer Responsibilities

## 4.1 UI Layer

The UI layer is responsible for presentation and user interaction.

It may:

- Display data.
- Capture user intent.
- Show progress.
- Show warnings and confirmations.
- Render execution plans.
- Display operation results.

It must not:

- Write metadata directly.
- Call FFmpeg directly.
- Call Audiobookshelf directly.
- Perform duplicate detection directly.
- Perform filesystem move/copy/delete operations directly.
- Contain core business rules.

The UI should communicate user intent by creating or invoking commands.

## 4.2 Command Layer

Commands coordinate meaningful user operations.

Examples:

- `SaveMetadataCommand`
- `CheckDuplicatesCommand`
- `ConvertBookCommand`
- `MoveToLibraryCommand`
- `ReplaceLibraryItemCommand`
- `RestoreArchivedCopyCommand`
- `RefreshAbsCacheCommand`

Commands are responsible for:

- Validation.
- Building an Execution Plan.
- Requesting user confirmation where appropriate.
- Executing service calls in the correct order.
- Creating operation records.
- Handling recoverable failure states.
- Reporting progress and results.

Every significant operation should be represented by a command.

## 4.3 Service Layer

Services implement business logic.

Examples:

- `Scanner`
- `MetadataService`
- `RulesEngine`
- `FFmpegManager`
- `ABSManager`
- `PlacementEngine`
- `DuplicateService`
- `ArchiveService`
- `SnapshotService`

Services must be UI-agnostic.

Services should receive input models and return output models, results, or domain events.

Services should avoid directly manipulating UI state.

## 4.4 Persistence Layer

SQLite is used for:

- Settings.
- Scan cache.
- ABS cache.
- Metadata snapshots.
- Operation history.
- Duplicate decisions.
- Indexes.
- Job state.

SQLite is not the source of truth for audiobook metadata.

The user's files and Audiobookshelf metadata remain authoritative depending on context.

Do not store cover art blobs in SQLite.

## 4.5 External Systems

External systems include:

- Filesystem.
- Mutagen.
- FFmpeg / FFprobe.
- Audiobookshelf API.
- Audiobookshelf metadata files.
- OS file browser / media playback services.

Access to external systems must be wrapped in services.

---

# 5. Dependency Rules

## 5.1 Allowed Dependencies

```text
ui → commands
ui → models
commands → services
commands → persistence
commands → models
services → persistence
services → models
services → external adapters
persistence → models
```

## 5.2 Forbidden Dependencies

```text
services → ui
persistence → ui
models → ui
models → services
rules → ui
scanner → metadata editor UI
duplicate service → conversion UI
```

## 5.3 Rule of Thumb

If a module needs to import PyQt6, it belongs in the UI layer.

If a module contains business logic, it should not import PyQt6.

---

# 6. Project Layout

Recommended source tree:

```text
src/
└── alchemist/
    ├── app/
    ├── commands/
    ├── core/
    ├── models/
    ├── persistence/
    ├── services/
    ├── rules/
    ├── jobs/
    ├── ui/
    └── utils/
```

Supporting directories:

```text
docs/
tests/
tools/
resources/
sample_data/
scripts/
```

---

# 7. Core Domain Concepts

## 7.1 Book

A Book is a logical audiobook.

It may be:

- A single-file book.
- A folder book made from multiple audio files.

A Book has an internal UUID assigned by Alchemist.

The UUID is stored in SQLite on discovery.

The UUID may be embedded into metadata only after the user performs an explicit save.

## 7.2 Track

A Track represents an audio file that belongs to a Book.

Folder books have multiple tracks.

Single-file books may have one track record.

## 7.3 Canonical Metadata

Alchemist uses a canonical metadata schema internally.

The canonical schema is stable.

Users may configure aliases and preferred write tags, but not canonical field names.

## 7.4 Execution Plan

An Execution Plan describes what a command intends to do before it does it.

Execution Plans should be human-readable and machine-recordable.

They are required for:

- Conversion.
- Replacement.
- Destructive library operations.
- Batch operations.

## 7.5 Operation Record

An Operation Record is a persistent record of what happened.

It includes:

- Operation type.
- Inputs.
- Execution plan.
- Steps performed.
- Logs.
- Result.
- Error state, if any.
- Recovery state, if applicable.

---

# 8. System Patterns

## 8.1 Command Pattern

Commands represent user intent.

Each command should support the following conceptual flow:

```text
validate()
build_execution_plan()
confirm_if_needed()
execute()
record_result()
```

Commands may be synchronous or asynchronous depending on operation cost.

Long-running commands must report progress.

## 8.2 Service Pattern

Services implement focused business capabilities.

A service should have one clear responsibility.

Services should be easy to unit test.

## 8.3 Repository Pattern

Database access should be isolated behind repositories.

Application logic should not scatter SQL throughout commands or services.

Examples:

- `BookRepository`
- `SettingsRepository`
- `SnapshotRepository`
- `OperationRepository`
- `AbsCacheRepository`
- `DuplicateDecisionRepository`

## 8.4 Rules Engine Pattern

Rules evaluate metadata and workflow health.

Rules should be small, independent, and additive.

A rule returns a result containing:

- Rule ID.
- Severity.
- Message.
- Affected field, if applicable.
- Suggested fix, if applicable.

Severity levels:

```text
INFO
WARNING
ERROR
BLOCKER
```

## 8.5 Event / Progress Pattern

Long-running services and commands should emit progress events.

Events may include:

- Started.
- Progress.
- Warning.
- Error.
- Completed.
- Cancelled.

The UI subscribes to these events and updates presentation state.

The service does not know how the UI displays them.

---

# 9. Data Flow

## 9.1 Startup Flow

```text
Application starts
Load settings
Open SQLite database
Load cached books
Populate UI from cache
Start background incremental scan
Start ABS cache refresh if stale/enabled
Update UI as background jobs produce results
```

Startup should not block on expensive scans.

## 9.2 Incoming Scan Flow

```text
Discover files/folders
Build fingerprints
Compare fingerprints to cache
Mark unchanged books as current
Queue new/changed books for enrichment
Update cache
Emit row-level updates
```

Routine scans must not re-read metadata for unchanged books.

## 9.3 Metadata Save Flow

```text
User edits metadata
User clicks Save
Command validates metadata
Command builds save plan
Command writes metadata
Command writes Alchemist UUID if first explicit save
Command stores snapshot
Command updates cache directly
Command logs operation
```

Saving one book must not trigger a full incoming scan.

## 9.4 Duplicate Check Flow

```text
User requests duplicate check
If ABS cache refreshing:
    Wait dialog is shown
If ABS cache ready:
    Duplicate indexes are queried
Results are shown
User makes resolution decision
Decision is persisted
```

## 9.5 Conversion Flow

```text
Validate book readiness
Build conversion plan
Show execution plan
Convert to staging
Verify output
Move to converted
Log result
```

Conversion must not write directly into the ABS library.

## 9.6 Replacement Flow

```text
Validate incoming replacement
Get ABS item and library ID
Validate current library copy
Archive current library copy
Validate archived copy
Trigger ABS scan
Poll until scan complete
Confirm item missing
Delete missing ABS item hard=true
Copy replacement into library
Validate copied replacement
Trigger ABS scan
Poll until complete
Record success
```

If replacement fails after archiving, restoration must be offered when possible.

---

# 10. Background Jobs

Long-running work should run outside the UI thread.

Examples:

- Incoming scans.
- ABS cache refresh.
- Duplicate batch checks.
- FFmpeg conversion.
- ABS scan polling.
- Replacement operations.

A background job should have:

- Job ID.
- Type.
- Status.
- Progress.
- Cancellation behavior.
- Result.
- Error details.

The UI must remain responsive during jobs.

---

# 11. Caching Strategy

Every expensive operation should have a cache and invalidation strategy.

| Operation | Cache | Invalidation |
|---|---|---|
| Incoming discovery | Book cache | Path/fingerprint changed |
| Metadata read | Metadata cache | Fingerprint changed or save performed |
| FFprobe technical data | Technical cache | Fingerprint changed |
| Chapter extraction | Chapter cache | Fingerprint changed |
| ABS library data | ABS cache | Manual refresh, stale cache, startup refresh |
| Duplicate lookups | In-memory indexes | ABS cache rebuilt |
| Execution plans | Operation records | New operation |

---

# 12. Identity Strategy

Natural keys are not stable enough to identify books.

Alchemist assigns an internal UUID when a book is first discovered.

The UUID is stored in SQLite.

On first explicit metadata save, the UUID may be embedded into the audio metadata using:

```text
TXXX:ALCHEMIST_ID
```

For folder books, the UUID may be written to each track.

The UUID should not be embedded during background scanning.

### 12.1 Embedded Alchemist Metadata

To maintain a stable identity across file moves and metadata changes,
Alchemist may embed application-specific metadata into audio files.

Current fields:

- ALCHEMIST_ID

Future application metadata should use the `ALCHEMIST_*` namespace to avoid collisions with third-party tags.

Application metadata is never used by Audiobookshelf and should not affect library organization or duplicate detection outside Alchemist.

---

# 13. Metadata Architecture

Alchemist must use a canonical internal metadata model.

The canonical business metadata model currently consists of the following fields.

- album
- title
- subtitle
- author
- narrator
- series
- series-part
- asin
- isbn
- publisher
- published_year
- description
- language
- genres
- explicit
- dramatic_audio
- target_bitrate
- target_channels

Tag aliases are configurable.

Canonical field names are not configurable.

When saving metadata, Alchemist writes preferred canonical tags while preserving legacy alias tags unless a later cleanup feature explicitly changes that behavior.

---

# 14. Audiobookshelf Integration

Audiobookshelf integration serves two roles:

1. Metadata and duplicate cache.
2. Library control operations.

ABS metadata cache should prefer `metadata.json` by default.

Embedded metadata may be used depending on configured source precedence.

The ABS API should be used for:

- Testing connection.
- Listing libraries.
- Triggering scans.
- Polling scan status.
- Confirming missing items.
- Deleting missing items with `hard=true`.
- Fetching item details when necessary.

The ABS API should not be used as the default bulk metadata source when filesystem metadata files are available.

---

# 15. FFmpeg Architecture

FFmpeg and FFprobe access must be wrapped by `FFmpegManager`.

The user may configure an FFmpeg executable directory.

If blank, Alchemist uses executables from the system PATH.

FFmpeg capability detection should include:

- FFmpeg version.
- FFprobe version.
- Available audio encoders.
- Whether `libfdk_aac` is available.
- Supported containers/features needed for M4B generation.

Default codec selection:

```text
libfdk_aac if available
aac otherwise
```

FFmpeg commands should be logged as part of operation records.

---

# 16. Placement Architecture

Placement should be template-driven.

Templates may include metadata tokens.

Missing tokens should be ignored gracefully.

Example tokens:

```text
%author%
%series%
%series_part%
%album%
%title%
%track%
%asin%
```

If `%track%` is an integer, it should be padded to two digits.

If `%track%` is not an integer, it should be used as-is.

Alternate duplicate placement affects only directory naming and must not modify metadata.

---

# 17. Error Handling

Errors should be actionable.

An error should answer:

- What failed?
- Where did it fail?
- What data was affected?
- Can the operation be retried?
- Can the operation be restored?
- What should the user do next?

Do not silently ignore exceptions.

Do not continue destructive workflows after a failed validation step.

---

# 18. Logging and Operation History

Every significant operation should produce an operation record.

Operation records should include:

- Operation type.
- Start time.
- End time.
- Status.
- Execution plan.
- Step log.
- Errors.
- Recovery options.

Logs should be useful for debugging without requiring reproduction.

---

# 19. Testing Philosophy

Core logic must be testable without launching the GUI.

Testing should prioritize:

- Metadata alias resolution.
- Scanner fingerprinting.
- Incremental scan behavior.
- Rules engine results.
- Placement template resolution.
- Duplicate matching.
- Execution plan generation.
- Error recovery paths.
- FFmpeg command construction.

The generated sample data corpus should be used for integration tests.

---

# 20. Cross-Platform Requirements

Alchemist must support:

- Windows
- Linux
- macOS

Packaging target:

- PyInstaller

Cross-platform concerns:

- Filesystem paths.
- Illegal filename characters.
- Executable discovery.
- Case sensitivity.
- File locking.
- OS media playback support.
- Theme rendering differences.

---

# 21. Things This Architecture Intentionally Avoids

Alchemist intentionally avoids:

- Automatic metadata writes.
- Direct Audiobookshelf database modification.
- Silent destructive operations.
- Full rescans after routine edits.
- Cover art blobs in SQLite.
- UI components directly calling FFmpeg.
- UI components directly calling ABS.
- Mutable natural keys for identity.
- Business logic hidden inside Qt callbacks.
- Unlogged destructive operations.

---

# 22. Relationship to Subsystem Specifications

This document governs all subsystem specifications.

Subsystem specifications should reference this document and must not contradict it without a new ADR.

Expected subsystem specifications:

- `2000-database.md`
- `3000-ui.md`
- `4000-metadata.md`
- `5000-scanning-engine.md`
- `6000-duplicate-detection.md`
- `7000-conversion-pipeline.md`
- `8000-placement-engine.md`
- `9000-command-framework.md`

---

# 23. Open Questions

The following items may require later ADRs or subsystem decisions:

- Exact job scheduling implementation.
- Exact PyQt threading model.
- Whether to support user-editable rule enable/disable states.
- Whether to support YAML-driven sample corpus generation.
- How much operation rollback should be automatic versus user-triggered.
- Whether to support plugin-style metadata providers in the future.

---

# 24. Acceptance Criteria for Architecture Compliance

A feature is architecturally compliant if:

- UI does not contain business logic.
- File and external operations are performed through services.
- Significant actions are command-driven.
- Expensive operations use caching where practical.
- Destructive operations have validation and confirmation.
- Operation history is recorded.
- Core logic is unit-testable.
- The feature follows the design principles and AGENTS.md.

---

# 25. Summary

Alchemist is designed as a cautious, explainable, maintainable audiobook management system.

The architecture exists to protect user data, reduce cognitive load, improve performance, and make future development easier.

When choosing between speed and safety, prefer safety.

When choosing between cleverness and clarity, prefer clarity.

When choosing between hidden automation and explainable planning, prefer explainable planning.
