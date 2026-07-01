# Project Philosophy

## Purpose

Alchemist exists to help users build and maintain a high-quality
audiobook library safely, predictably, and with confidence.

It is **not** simply a metadata editor or a graphical front-end for
FFmpeg. It is a metadata management platform that assists users in
making informed decisions while protecting their data.

------------------------------------------------------------------------

# The Problem We Are Solving

Managing large audiobook libraries is repetitive, error-prone, and often
destructive. Existing tools tend to focus on individual tasks rather
than the entire workflow.

Alchemist aims to unify metadata management, duplicate detection,
conversion, and library operations into a single coherent application.

------------------------------------------------------------------------

# Our Philosophy

## Safety First

User data is valuable.

Whenever practical:

-   Archive before destructive operations.
-   Validate before executing.
-   Verify after completion.
-   Provide recovery paths.

The safest reasonable behavior should always be the default.

------------------------------------------------------------------------

## Explain Before Executing

Users should understand:

-   what will happen,
-   why it will happen,
-   and how it will happen.

Execution Plans are a core feature, not an afterthought.

------------------------------------------------------------------------

## Reduce Cognitive Load

The application should remember rules so users do not have to.

Users should spend their time making decisions, not hunting for
information.

Metadata Health, validation rules, execution plans, and diagnostics all
exist to reduce mental effort.

------------------------------------------------------------------------

## Optimize for Maintainability

Code should remain understandable years after it is written.

Prefer:

-   simple architecture
-   explicit workflows
-   well-defined responsibilities
-   small, testable components

Avoid clever solutions that obscure intent.

------------------------------------------------------------------------

## Build Systems, Not Utilities

Each subsystem should solve one problem well while integrating cleanly
with the rest of the application.

The architecture should encourage extension through new commands,
services, rules, and specifications rather than invasive rewrites.

------------------------------------------------------------------------

# Lessons Carried Forward

Alchemist exists because previous projects taught important lessons:

-   UI responsiveness must never depend on rescanning the filesystem.
-   Canonical metadata should exist independently of tag formats.
-   Cover art should not be cached in SQLite.
-   Every expensive operation needs a cache and an invalidation
    strategy.
-   Destructive actions should be recoverable.
-   Architecture should be designed before implementation.

These lessons are considered project principles.

------------------------------------------------------------------------

# How to Evaluate New Features

Before adding a feature, ask:

1.  Does it make the user's library safer?
2.  Does it reduce repetitive work?
3.  Does it fit the existing architecture?
4.  Can it be explained clearly through an Execution Plan?
5.  Is it maintainable?
6.  Does it simplify the system rather than complicate it?

If the answer to most of these questions is "no," reconsider the design.

------------------------------------------------------------------------

# Definition of Success

A successful Alchemist feature is one that:

-   protects user data,
-   improves metadata quality,
-   scales to large libraries,
-   is pleasant to maintain,
-   and leaves the user more informed than before the operation began.

------------------------------------------------------------------------

# Final Principle

Alchemist should be software that its author is proud to maintain five
years from now.

Every architectural decision should optimize for long-term clarity,
correctness, maintainability, and trust rather than short-term
convenience.
