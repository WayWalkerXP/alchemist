# ADR-0001 --- Architectural Foundation

**Status:** Accepted

**Date:** 2026-07-02

------------------------------------------------------------------------

# Context

Alchemist was created after several previous audiobook management
projects demonstrated recurring architectural problems.

While those applications successfully solved individual problems, they
gradually evolved into collections of tightly-coupled workflows where
user interfaces, business logic, metadata handling, filesystem
operations, and external tools became increasingly intertwined.

As new features were added, unintended consequences became more common:

-   Business logic became coupled to the user interface.
-   Similar workflows were implemented multiple times.
-   Safety mechanisms became inconsistent.
-   Metadata rules leaked throughout the codebase.
-   Users were occasionally forced to perform workflow steps outside the
    application.
-   Recovery from mistakes became increasingly difficult.

These experiences demonstrated that the project required an intentional
architecture rather than an accumulation of utilities.

The primary responsibility of Alchemist is not simply to manipulate
metadata or invoke FFmpeg. Its responsibility is to safely guide users
through the complete lifecycle of preparing, validating, converting,
organizing, and maintaining an audiobook library.

This responsibility demands an architecture that prioritizes
correctness, safety, explainability, maintainability, and long-term
evolution over short-term implementation convenience.

------------------------------------------------------------------------

# Decision

Alchemist adopts a layered, command-driven architecture built around
explicit workflows, canonical metadata, and execution planning.

The architecture is governed by the following principles.

## 1. Protect the Library

Protecting the user's audiobook library is the primary architectural
objective.

Every significant architectural decision should ultimately support this
goal.

Performance, convenience, and automation are important, but they are
always secondary to protecting user data, metadata integrity, and
library consistency.

------------------------------------------------------------------------

## 2. Files are the Source of Truth

Audiobook files and their associated metadata remain the authoritative
representation of the user's collection.

SQLite exists to improve performance, retain history, support planning,
and cache expensive operations.

It must never become the authoritative source of audiobook metadata.

------------------------------------------------------------------------

## 3. User Intent Drives All Changes

Alchemist exists to assist users in making informed decisions.

It does not silently rewrite metadata, reorganize libraries, or perform
destructive operations without explicit user intent.

Automation is encouraged when it follows user-defined workflows, but
automation must never remove user responsibility for significant
decisions.

------------------------------------------------------------------------

## 4. Commands Represent Workflows

User actions are represented as Commands.

Commands coordinate complete workflows by validating inputs,
constructing execution plans, invoking services in the correct order,
handling failures, recording operation history, and producing consistent
results.

Commands describe *how work flows through the system.*

Business capabilities remain encapsulated within Services.

------------------------------------------------------------------------

## 5. Services Own Business Logic

Services implement focused business capabilities.

Each service should solve one problem well while remaining independent
of user interface concerns.

Services should be reusable across graphical interfaces, command-line
tools, automated pipelines, and future integration points.

------------------------------------------------------------------------

## 6. Execution Plans are First-Class Citizens

Before significant changes are performed, Alchemist constructs an
Execution Plan describing:

-   what will happen,
-   why it will happen,
-   how it will happen,
-   and what risks or recovery options exist.

Execution Plans are a core architectural concept rather than a
user-interface feature.

They provide transparency, simplify testing, improve diagnostics, and
create consistent operation records.

------------------------------------------------------------------------

## 7. Canonical Metadata

Internally, Alchemist reasons about metadata using a canonical model
independent of any external tagging format.

External formats, tag names, metadata files, and APIs are adapters to
this canonical model rather than the model itself.

This allows the application to evolve independently of individual
metadata standards while presenting consistent behavior throughout the
system.

Canonical metadata consists of three categories:

-   Canonical Business Metadata (CBM)
-   Canonical Technical Metadata (CTM)
-   Canonical Application Metadata (CAM)

------------------------------------------------------------------------

## 8. Friction Should Be Intentional

The architecture intentionally introduces friction only when it improves
safety.

Confirmation dialogs, validation steps, execution plans, backups, and
recovery workflows exist to reduce the likelihood and impact of user
mistakes.

Unnecessary friction should be removed.

Protective friction should be embraced.

------------------------------------------------------------------------

## 9. Recoverability Over Convenience

Whenever practical, workflows should support recovery.

Examples include:

-   validation before execution,
-   snapshots before metadata changes,
-   archive-before-replace workflows,
-   operation history,
-   rollback where practical.

When recovery is impossible, the user should understand why before
proceeding.

------------------------------------------------------------------------

## 10. Components Communicate Through Stable Contracts

Subsystems should expose clear responsibilities, well-defined inputs,
and predictable outputs.

Implementation details should remain encapsulated.

This allows components to evolve independently while maintaining
consistent behavior across the application.

Well-defined contracts improve maintainability, testing, documentation,
and contributor productivity.

------------------------------------------------------------------------

# Rationale

This architecture intentionally favors clarity over cleverness.

Although it introduces additional structure compared to utility-style
applications, that structure provides significant long-term benefits.

The architecture enables:

-   safer workflows,
-   reusable business logic,
-   comprehensive testing,
-   incremental development,
-   predictable behavior,
-   clearer documentation,
-   easier extension,
-   and better long-term maintainability.

Most importantly, it allows the application to guide users through
complex workflows while maintaining confidence that their library
remains protected.

------------------------------------------------------------------------

# Alternatives Considered

## Utility-Based Architecture

A collection of independent utilities connected through the user
interface.

Rejected because business rules become duplicated, workflows become
inconsistent, and features become increasingly difficult to maintain.

------------------------------------------------------------------------

## UI-Centric Architecture

Allow the graphical interface to directly coordinate filesystem
operations, metadata editing, FFmpeg, and Audiobookshelf interactions.

Rejected because user interface code becomes responsible for business
workflows, reducing testability and increasing coupling.

------------------------------------------------------------------------

## Database-Centric Architecture

Treat SQLite as the authoritative representation of audiobook metadata.

Rejected because the authoritative metadata already exists within user
files.

Maintaining two competing sources of truth unnecessarily increases
synchronization complexity and failure modes.

------------------------------------------------------------------------

## Automatic Decision-Making

Allow the application to automatically make metadata, placement, or
replacement decisions without user involvement.

Rejected because preserving user trust is more valuable than eliminating
a small amount of interaction.

Automation should execute user-defined workflows rather than replace
user judgment.

------------------------------------------------------------------------

# Consequences

This decision establishes several long-term architectural expectations.

Positive consequences include:

-   safer workflows,
-   consistent behavior,
-   modular implementation,
-   simpler testing,
-   reusable services,
-   predictable feature development,
-   improved documentation,
-   and clearer subsystem boundaries.

Tradeoffs include:

-   additional abstraction,
-   more project structure,
-   greater upfront design effort,
-   and workflows that may require additional planning before execution.

These tradeoffs are accepted because they directly support the project's
primary responsibility of protecting the user's library.

------------------------------------------------------------------------

# Future Decisions

This ADR establishes the architectural foundation for future decisions,
including:

-   Canonical Metadata Model
-   Identity Strategy
-   Caching Strategy
-   Background Job Architecture
-   Pipeline Automation
-   Plugin Architecture
-   Rules Engine Evolution

Additional ADRs may refine individual architectural areas but should
remain consistent with the principles established by this document.

------------------------------------------------------------------------

# References

-   Project Philosophy
-   Alchemist Architecture Guide
-   1000 -- System Architecture Specification

------------------------------------------------------------------------

# Final Principle

Alchemist is not merely a collection of audiobook utilities.

It is a system designed to help users improve and maintain their
audiobook libraries with confidence.

When architectural tradeoffs arise, the preferred solution is the one
that best protects the user's library while remaining understandable,
maintainable, and transparent.
