# ADR-0002 — Canonical Metadata and Metadata Resolution

**Status:** Accepted

**Date:** 2026-07-02

---

# Context

Metadata is the foundation upon which every major subsystem of Alchemist is built.

Scanning, metadata editing, duplicate detection, conversion, placement, Audiobookshelf integration, validation, diagnostics, and future automation all depend on a consistent understanding of metadata.

External metadata, however, exists in many different forms:

- MP4 atoms
- ID3 tags
- Audiobookshelf metadata
- OPF files
- NFO files
- Folder structure
- Filename parsing
- Online metadata providers
- User edits

Each source uses different field names, different capabilities, and varying levels of completeness and quality.

Allowing the remainder of the application to reason directly about these external representations would tightly couple every subsystem to every metadata format and make future maintenance increasingly difficult.

A consistent internal metadata model is therefore required.

---

# Decision

Alchemist adopts a Canonical Metadata Model that is independent of any external metadata format.

The application reasons exclusively in terms of canonical metadata.

External metadata exists only as input to, or output from, the canonical model.

---

# Architectural Principles

## 1. Metadata Belongs to Books

The canonical unit of the system is a **Book**.

A Book consists of one or more **Tracks**.

A single-file audiobook is represented as a Book containing one Track.

A multi-file audiobook is represented as a Book containing multiple ordered Tracks.

Metadata is therefore modeled around the logical audiobook rather than around individual files.

---

## 2. Metadata Exists in Three Categories

Canonical metadata is divided into three architectural categories.

### Canonical Business Metadata (CBM)

Describes the audiobook itself.

Examples include authors, title, narrator, series, publication information, genres, and identifiers.

Business metadata generally belongs to the Book.

---

### Canonical Technical Metadata (CTM)

Describes the media used to represent the audiobook.

Examples include duration, codec, bitrate, sample rate, channels, track count, and chapter information.

Technical metadata may exist at both the Book and Track level.

---

### Canonical Application Metadata (CAM)

Describes Alchemist's relationship to the audiobook.

Examples include application identifiers, snapshots, discovery timestamps, validation state, and operation history references.

Application metadata is never intended for consumption by external applications unless explicitly documented.

---

## 3. External Metadata is Never Canonical

Metadata originating from external systems remains external regardless of its format.

Examples include:

- ID3 tags
- MP4 atoms
- Audiobookshelf metadata
- OPF files
- NFO files
- Folder names
- Filenames
- Online metadata providers

These formats are implementation details.

Business logic must not reason directly about external field names.

---

## 4. Alias Resolution is a Separate Architectural Concern

External metadata is translated into canonical metadata through Alias Resolution.

Alias Resolution maps multiple external representations onto a single canonical field.

Examples include:

- `artist`
- `album-artist`
- `TPE1`

all resolving to the same canonical Author field.

Alias Resolution performs normalization only.

It does not perform business decisions, validation, or metadata cleanup.

---

## 5. Canonical Metadata is Stable

Canonical metadata represents the vocabulary used throughout Alchemist.

Subsystems communicate using canonical metadata rather than external tag names.

The canonical vocabulary evolves only through architectural decisions.

The complete canonical field definitions are maintained by the Metadata Specification.

---

## 6. Metadata Providers are Independent

Metadata may originate from multiple providers.

Examples include:

- embedded metadata
- Audiobookshelf metadata
- OPF/NFO files
- folder parsing
- filename parsing
- online metadata services
- user edits

Providers are independent of the canonical model.

New providers should be introducible without requiring changes to business logic.

---

## 7. Source Precedence is Policy

Multiple providers may supply values for the same canonical field.

The process used to determine which value becomes canonical is governed by Metadata Resolution Policy.

This policy is intentionally separate from the metadata architecture.

The exact precedence rules are defined by subsystem specifications and user configuration where appropriate.

---

## 8. Canonical Values Preserve Provenance

Every resolved canonical value should retain information describing its origin.

This information exists to explain how a value entered the system.

Examples include:

- originating provider
- originating field or tag
- original value
- resolution timestamp
- transformation history

Provenance allows Alchemist to explain metadata decisions, diagnose unexpected results, improve metadata cleanup rules, and support future auditing capabilities.

---

## 9. Derived Values Must Remain Explainable

Some canonical values are copied directly from external metadata.

Others are produced by transformation.

Examples include:

- author normalization
- title cleanup
- removal of marketing text
- series normalization
- language normalization

Derived values must preserve sufficient provenance to explain:

- the original value,
- the transformation performed,
- and the resulting canonical value.

Metadata cleanup must never become an opaque process.

---

## 10. Reading and Writing are Independent Processes

Reading metadata and writing metadata are separate architectural concerns.

Reading resolves external metadata into the canonical model.

Writing translates canonical metadata into one or more external representations.

Neither process should dictate the structure of the canonical model.

---

## 11. Compatibility Does Not Define Architecture

Audiobookshelf compatibility is a primary design objective.

The Audiobookshelf metadata model serves as an important compatibility target and informs preferred metadata mappings.

However, Audiobookshelf does not define Alchemist's internal metadata architecture.

The canonical model exists independently of any individual application or metadata standard.

---

## 12. Metadata Architecture Supports Multiple Library Formats

The canonical model supports both:

- single-file audiobooks
- multi-track audiobooks

Single-file M4B remains the preferred default output format for Alchemist workflows.

However, the architecture intentionally treats both representations as valid Books.

This allows future workflows to support very large audiobooks, chapter-based libraries, and user preferences without altering the canonical model.

---

# Rationale

Separating canonical metadata from external representations provides several important advantages.

It allows:

- independent evolution of metadata providers,
- simpler business logic,
- easier testing,
- cleaner subsystem boundaries,
- improved diagnostics,
- safer metadata transformations,
- future metadata providers,
- and clearer explanations to users.

The resulting architecture reduces coupling throughout the application and establishes metadata as a stable domain model rather than an implementation detail.

---

# Alternatives Considered

## Format-Specific Metadata

Allow each subsystem to reason directly about MP4 atoms, ID3 tags, Audiobookshelf fields, and other external formats.

Rejected because every subsystem would become tightly coupled to every supported metadata format.

---

## Audiobookshelf as the Internal Model

Adopt Audiobookshelf field names directly throughout the application.

Rejected because Alchemist should remain independent of any single external application while maintaining compatibility with it.

---

## Metadata Without Provenance

Retain only resolved values.

Rejected because metadata transformations would become difficult to explain, diagnose, and improve over time.

---

# Consequences

This decision establishes that:

- every subsystem communicates using canonical metadata,
- external metadata formats remain isolated,
- metadata providers are interchangeable,
- metadata transformations remain explainable,
- provenance becomes part of the metadata architecture,
- and future metadata standards can be supported without redesigning the application.

---

# Out of Scope

This ADR intentionally does not define:

- the complete canonical field list,
- tag mappings,
- metadata precedence rules,
- provider implementations,
- database schema,
- metadata editor behavior,
- or serialization formats.

These are defined by subsystem specifications.

---

# References

- ADR-0001 — Architectural Foundation
- 1000 — System Architecture Specification
- 4000 — Metadata Specification (future)
- Audiobookshelf Documentation – File Metadata
- Audiobookshelf Documentation – Audiobook Tracks

---

# Final Principle

Metadata should be understandable independent of where it originated.

The application should reason about the audiobook itself—not about the format in which its metadata happened to be stored.

Every metadata decision should remain explainable, reproducible, and ultimately serve the primary architectural objective of protecting and improving the user's library.