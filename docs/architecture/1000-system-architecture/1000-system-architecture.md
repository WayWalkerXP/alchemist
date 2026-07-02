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

This specification implements and must remain consistent with the governing Architecture Decision Records:

- ADR-0001 — Architectural Foundation
- ADR-0002 — Canonical Metadata and Metadata Resolution
- ADR-0003 — Identity Strategy
- ADR-0004 — Execution Plans and Operation Records

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

When goals conflict, protecting the user's library takes precedence.

---

# 3. Core Architecture

Alchemist follows a layered architecture.

```text
UI Layer
   ↓
Command Layer
   ↓
Execution Planning / Execution Layer
   ↓
Service Layer
   ↓
Persistence / External Systems
```

The direction of dependency is downward only.

Higher layers may depend on lower layers.

Lower layers must not depend on higher layers.

The conceptual workflow is:

```text
User Intent
   ↓
Command
   ↓
Execution Plan
   ↓
Approval / Decision Gates
   ↓
Execution
   ↓
Operation Record
```

---

# 4. Layer Responsibilities

## 4.1 UI Layer

The UI layer is responsible for presentation and user interaction.

It may:

- Display data.
- Capture user intent.
- Show progress.
- Show warnings and confirmations.
- Render Execution Plans.
- Display Operation Records and operation results.
- Collect user decisions at Decision Gates.

It must not:

- Write metadata directly.
- Call FFmpeg directly.
- Call Audiobookshelf directly.
- Perform duplicate detection directly.
- Perform filesystem move/copy/delete operations directly.
- Contain core business rules.
- Execute service workflows directly.

The UI communicates user intent by invoking Commands and presenting the resulting Execution Plans.

## 4.2 Command Layer

Commands translate user intent into Execution Plans.

Examples:

- `SaveMetadataCommand`
- `CheckDuplicatesCommand`
- `ConvertBookCommand`
- `MoveToLibraryCommand`
- `ReplaceLibraryItemCommand`
- `RestoreArchivedCopyCommand`
- `RefreshAbsCacheCommand`

Commands are responsible for:

- Validating command inputs.
- Gathering required context.
- Building Execution Plans.
- Declaring approval requirements.
- Declaring Decision Gates when human judgment is required.
- Returning plan-generation errors when a plan cannot be built safely.

Commands are workflow generators, not workflow executors.

Every significant operation should be represented by a Command.

## 4.3 Execution Planning / Execution Layer

Execution Plans are first-class architectural objects.

The execution layer is responsible for:

- Validating an approved plan is still valid.
- Executing approved plan steps.
- Pausing at Decision Gates.
- Emitting progress events.
- Recording step outcomes.
- Producing Operation Records.
- Stopping safely when the environment invalidates the approved plan.

Approved Execution Plans are immutable. If the environment changes in a way that could affect the outcome, the plan must be invalidated and rebuilt.

## 4.4 Service Layer

Services implement focused business capabilities.

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

## 4.5 Persistence Layer

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

For local audiobook metadata, the user's audio files and associated sidecar metadata files are the source of truth.

Audiobookshelf may be treated as an external reference source or operational system, but Alchemist must not treat ABS cache data as authoritative over local files unless a user explicitly chooses an ABS-sourced update through an Execution Plan.

Do not store cover art blobs in SQLite.

## 4.6 External Systems

External systems include:

- Filesystem.
- Mutagen.
- FFmpeg / FFprobe.
- Audiobookshelf API.
- Audiobookshelf metadata files.
- OPF / NFO / sidecar metadata files.
- OS file browser / media playback services.

Access to external systems must be wrapped in services or external adapters.

---

# 5. Dependency Rules

## 5.1 Allowed Dependencies

```text
ui → commands
ui → models
commands → planning
commands → services
commands → persistence
commands → models
planning → services
planning → persistence
planning → models
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
external adapters → ui
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
    ├── domain/
    ├── external/
    ├── jobs/
    ├── models/
    ├── persistence/
    ├── planning/
    ├── rules/
    ├── services/
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

`domain/` contains pure domain concepts and logic.

`external/` contains adapters for systems outside Alchemist.

`planning/` contains Execution Plan, Decision Gate, execution, and Operation Record concepts.

`utils/` must remain generic and must not become a business-logic dumping ground.

---

# 7. Core Domain Concepts

## 7.1 Book

A Book is a logical audiobook.

It may be:

- A single-file book.
- A folder book made from multiple audio files.
- A multi-part book made from multiple audio files.

A Book has an `ALCHEMIST_ID` assigned by Alchemist.

The ID is stored internally on discovery.

The ID is embedded into file metadata only after the user performs an explicit metadata write.

## 7.2 Track

A Track represents an audio file that belongs to a Book.

Folder books and multi-part books have multiple Tracks.

Single-file books may have one Track record.

Tracks belonging to multi-track Books have `ALCHEMIST_TRACK_ID` values.

Single-file books do not require embedded `ALCHEMIST_TRACK_ID` values.

## 7.3 Canonical Metadata

Alchemist uses a canonical metadata model internally.

Canonical metadata is divided into:

- Canonical Business Metadata (CBM)
- Canonical Technical Metadata (CTM)
- Canonical Application Metadata (CAM)

The canonical model is stable.

Users may configure aliases and preferred write tags, but not canonical field names.

The complete canonical field list is defined in `4000-metadata.md` rather than duplicated here.

## 7.4 Execution Plan

An Execution Plan describes approved or proposed work before it happens.

Execution Plans are human-readable, machine-recordable, serializable, testable, and executable.

They are required for:

- Metadata writes.
- Conversion.
- Replacement.
- Move/copy/delete operations.
- Destructive library operations.
- Batch operations.
- Operations that call external systems and change state.

Simple read-only operations do not require Execution Plans.

## 7.5 Decision Gate

A Decision Gate is a point inside an Execution Plan where human judgment or explicit policy is required before execution can continue.

Examples:

- Selecting one metadata match from several candidates.
- Confirming a risky metadata change.
- Choosing how to handle a duplicate.
- Confirming replacement after validation warnings.

## 7.6 Operation Record

An Operation Record is the historical record of an executed Execution Plan.

It includes:

- The approved Execution Plan.
- Operation type.
- Inputs.
- Steps performed.
- User decisions.
- Logs.
- Result.
- Error state, if any.
- Recovery state, if applicable.

Operation Records provide traceability rather than merely logging events.

---

# 8. System Patterns

## 8.1 Command Pattern

Commands represent user intent and generate Execution Plans.

Conceptual flow:

```text
receive_intent()
validate_inputs()
gather_context()
build_execution_plan()
return_plan_or_errors()
```

Commands must not directly display confirmation dialogs or execute workflow steps.

## 8.2 Execution Plan Pattern

Execution Plans represent proposed work.

Conceptual flow:

```text
build_plan()
validate_plan()
present_plan()
approve_plan()
execute_approved_plan()
record_operation()
```

Once approved, a plan is immutable.

Execution should not recalculate materially different actions after approval. If the plan is no longer valid, execution must stop and the plan must be rebuilt.

## 8.3 Service Pattern

Services implement focused business capabilities.

A service should have one clear responsibility.

Services should be easy to unit test.

## 8.4 Repository Pattern

Database access should be isolated behind repositories.

Application logic should not scatter SQL throughout commands or services.

Examples:

- `BookRepository`
- `SettingsRepository`
- `SnapshotRepository`
- `OperationRepository`
- `AbsCacheRepository`
- `DuplicateDecisionRepository`

## 8.5 Rules Engine Pattern

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

Identity collisions are BLOCKER-level health issues.

## 8.6 Event / Progress Pattern

Long-running services, jobs, and plan executions should emit progress events.

Events may include:

- Started.
- Progress.
- Warning.
- Error.
- Completed.
- Cancelled.
- Paused at Decision Gate.
- Plan invalidated.

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
Read embedded Alchemist IDs when present
Assign internal IDs for newly discovered books/tracks
Compare metadata fingerprints to cache
Mark unchanged books as current
Queue new/changed books for enrichment
Update cache
Emit row-level updates
```

Routine scans must not re-read metadata for unchanged books.

Scanning must not write metadata to user files.

## 9.3 Metadata Save Flow

```text
User edits metadata
User clicks Save
Command validates inputs
Command builds metadata save plan
UI presents plan / warnings when required
User approves plan
Execution layer writes metadata
Execution layer writes Alchemist IDs if first explicit save
Execution layer stores snapshot
Execution layer updates cache directly
Execution layer records operation
```

Saving one book must not trigger a full incoming scan.

## 9.4 Duplicate Check Flow

```text
User requests duplicate check
Command builds duplicate check plan
If ABS cache refreshing:
    Decision/wait state is shown
If ABS cache ready:
    Duplicate indexes are queried
Results are shown
User makes resolution decision
Decision is persisted
Operation record is updated
```

## 9.5 Conversion Flow

```text
Validate book readiness
Build conversion plan
Show Execution Plan
Approve plan
Convert to staging
Verify output
Move to converted
Record operation
```

Conversion must not write directly into the ABS library.

## 9.6 Replacement Flow

```text
Validate incoming replacement
Get ABS item and library ID
Validate current library copy
Build replacement plan
Show Execution Plan
Approve plan
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
- Execution Plan execution.

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
| Execution plans | Operation records | New operation or plan invalidation |

---

# 12. Identity Strategy

Natural keys are not stable enough to identify Books.

Alchemist assigns an `ALCHEMIST_ID` when a Book is first discovered.

The ID is stored internally immediately.

The ID is written to audio metadata only during an explicit user-approved metadata write.

Multi-track Books also receive `ALCHEMIST_TRACK_ID` values for each Track.

For multi-track Books, the first approved metadata save writes:

- the shared `ALCHEMIST_ID` to every Track,
- the appropriate `ALCHEMIST_TRACK_ID` to each individual Track.

Single-file Books do not require embedded `ALCHEMIST_TRACK_ID` values.

The ID should not be embedded during background scanning.

### 12.1 Embedded Alchemist Metadata

To maintain a stable identity across file moves and metadata changes, Alchemist may embed application-specific metadata into audio files.

Current fields:

- `ALCHEMIST_ID`
- `ALCHEMIST_TRACK_ID`

Future application metadata should use the `ALCHEMIST_*` namespace to avoid collisions with third-party tags.

Application metadata is never used by Audiobookshelf and should not affect library organization or duplicate detection outside Alchemist.

### 12.2 Identity Health

Duplicate embedded `ALCHEMIST_ID` values are identity collisions.

Identity collisions are BLOCKER-level metadata health issues.

Malformed embedded Alchemist IDs are metadata health issues.

Alchemist must not silently resolve identity collisions or invalid application identifiers.

---

# 13. Metadata Architecture

Alchemist must use a canonical internal metadata model.

The canonical model is divided into:

- Canonical Business Metadata (CBM)
- Canonical Technical Metadata (CTM)
- Canonical Application Metadata (CAM)

External metadata formats are not canonical.

Alias Resolution maps external tags, fields, sidecar files, filenames, folder structures, and provider data into canonical metadata.

Canonical values should preserve provenance describing where they came from and what transformations were applied.

Derived values produced by cleanup or normalization must remain explainable.

Tag aliases are configurable.

Canonical field names are not configurable.

The complete canonical field list and tag mappings belong in `4000-metadata.md`.

When saving metadata, Alchemist writes preferred compatible tags while preserving existing alias tags unless an explicit cleanup feature changes that behavior through an approved Execution Plan.

---

# 14. Audiobookshelf Integration

Audiobookshelf integration serves two roles:

1. Metadata and duplicate cache.
2. Library control operations.

ABS compatibility is a primary design objective, but ABS does not define Alchemist's internal metadata architecture.

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

FFmpeg commands should be logged as part of Operation Records.

---

# 16. Placement Architecture

Placement should be template-driven.

Templates may include metadata tokens.

Missing tokens should be ignored gracefully.

Example tokens:

```text
%author%
%series%
%series-part%
%series_part%
%album%
%title%
%track%
%asin%
```

Template tokens are user-facing aliases and may differ from canonical field names when needed for readability or filename safety.

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

Do not continue executing an approved plan after the environment changes in a way that invalidates it.

---

# 18. Logging and Operation History

Every significant operation should produce an Operation Record.

Operation Records should include:

- Operation type.
- Start time.
- End time.
- Status.
- Approved Execution Plan.
- Step log.
- User decisions.
- Errors.
- Recovery options.

Logs should be useful for debugging without requiring reproduction.

Operation Records are historical records of executed plans, not merely text logs.

---

# 19. Testing Philosophy

Core logic must be testable without launching the GUI.

Testing should prioritize:

- Metadata alias resolution.
- Metadata provenance.
- Scanner fingerprinting.
- Incremental scan behavior.
- Rules engine results.
- Placement template resolution.
- Duplicate matching.
- Execution Plan generation.
- Plan invalidation.
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
- Commands executing workflows directly.
- Treating ABS metadata as Alchemist's internal metadata model.

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
- Exact pipeline automation model.

---

# 24. Acceptance Criteria for Architecture Compliance

A feature is architecturally compliant if:

- UI does not contain business logic.
- File and external operations are performed through services or external adapters.
- Significant actions are command-driven.
- Commands generate Execution Plans rather than executing workflows directly.
- Significant state-changing operations produce Execution Plans.
- Approved plans are not silently changed during execution.
- Expensive operations use caching where practical.
- Destructive operations have validation and confirmation.
- Operation history is recorded.
- Core logic is unit-testable.
- The feature follows the design principles, ADRs, and AGENTS.md.

---

# 25. Summary

Alchemist is designed as a cautious, explainable, maintainable audiobook workflow system.

The architecture exists to protect user data, reduce cognitive load, improve performance, and make future development easier.

When choosing between speed and safety, prefer safety.

When choosing between cleverness and clarity, prefer clarity.

When choosing between hidden automation and explainable planning, prefer explainable planning.
