# ADR-0003 --- Identity Strategy

**Status:** Accepted

**Date:** 2026-07-02

------------------------------------------------------------------------

# Context

Alchemist manages logical audiobooks rather than individual files. Books
may be represented as a single audio file or as multiple tracks. The
application must recognize the same Book across file moves, metadata
updates, conversions, and library operations while avoiding accidental
identity collisions.

Natural identifiers such as title, author, filename, path, or ASIN are
not sufficiently stable to serve as the application's primary identity.

A dedicated identity strategy is therefore required.

------------------------------------------------------------------------

# Decision

Alchemist adopts application-owned identifiers that are independent of
external metadata standards.

Two identifiers exist:

-   **ALCHEMIST_ID** -- identifies a logical Book.
-   **ALCHEMIST_TRACK_ID** -- identifies an individual Track within a
    multi-track Book.

------------------------------------------------------------------------

# Architectural Principles

## 1. Identity Belongs to the Book

Every discovered Book is assigned an `ALCHEMIST_ID`. The identifier
remains stable for the lifetime of the logical Book regardless of
filename, directory structure, metadata changes, or library placement.

## 2. Tracks Have Independent Identity

Each Track belonging to a multi-track Book is assigned its own
`ALCHEMIST_TRACK_ID`.

Single-file books do not require an embedded track identifier.

## 3. Identity Exists Before It Is Embedded

When a Book is first discovered:

-   Generate a new `ALCHEMIST_ID` if one is not already embedded.
-   Store the identifier internally.
-   Do not modify user files.

Identity may therefore exist inside Alchemist before it exists inside
the audiobook itself.

## 4. Identity Is Embedded Only With User Approval

Alchemist never writes application identifiers during scanning.

`ALCHEMIST_ID` and `ALCHEMIST_TRACK_ID` are embedded only as part of an
explicit, user-approved metadata write.

## 5. Folder Books Are Embedded Consistently

For multi-track books, the first approved metadata save writes:

-   the shared `ALCHEMIST_ID` to every track,
-   the appropriate `ALCHEMIST_TRACK_ID` to each individual track.

## 6. Identity Is Portable

Once embedded, application identity travels with the audiobook.

Before embedding, identity may only be recovered through fingerprinting,
cached history, or path history.

## 7. External Identifiers Are Not Identity

ASIN, ISBN, filenames, and folder names are valuable for matching and
duplicate detection but are never the application's primary identity.

## 8. Identity Collisions Are Blockers

Duplicate embedded `ALCHEMIST_ID` values are BLOCKER-level metadata
health issues.

Alchemist must never silently resolve identity collisions.

## 9. Invalid Application Identifiers

Malformed embedded identifiers are metadata health issues.

Repair requires user approval.

## 10. Conversion Preserves Identity

Converting between folder books and single-file books preserves
`ALCHEMIST_ID`.

`ALCHEMIST_TRACK_ID` values need not be embedded in resulting
single-file books, although internal history may be retained.

------------------------------------------------------------------------

# Rationale

Application-owned identifiers provide a stable identity that survives
changes to filenames, metadata, directory structure, and external
providers.

Separating Book identity from Track identity allows Alchemist to support
both single-file and multi-track audiobooks without compromising the
logical model.

------------------------------------------------------------------------

# Alternatives Considered

## ASIN as Primary Identity

Rejected because many books lack ASINs and Audible ASINs may change over
time.

## Filename or Path as Identity

Rejected because users routinely rename and relocate audiobook files.

## Immediate Identity Embedding

Rejected because it modifies user files during discovery without
explicit approval.

------------------------------------------------------------------------

# Consequences

-   Every Book has a stable application identity.
-   Multi-track Books have stable Track identities.
-   Identity survives moves and conversions once embedded.
-   Scanning never modifies user files.
-   Identity conflicts are treated as metadata health issues.

------------------------------------------------------------------------

# Out of Scope

This ADR does not define UUID format, fingerprinting algorithms,
database schema, collision repair workflow, or UI behavior.

------------------------------------------------------------------------

# References

-   ADR-0001 --- Architectural Foundation
-   ADR-0002 --- Canonical Metadata and Metadata Resolution
-   1000 --- System Architecture Specification

------------------------------------------------------------------------

# Final Principle

Identity belongs to the logical audiobook, not to its filename,
location, or external metadata. Once established, that identity should
remain stable, portable, explainable, and under the user's control.
