# 9000 - Command Framework Specification

## Status

Preliminary Architectural Skeleton

## Purpose

Define command lifecycle, execution plans, operation records, decision gates, plan execution, cancellation, recovery, dependency injection, and testing.

## Governing Decisions

This specification must implement and remain consistent with:

- ADR-0001 — Architectural Foundation
- ADR-0004 — Execution Plans and Operation Records
- 1000 — System Architecture Specification

## Core Model

The command framework is based on the following flow:

```text
User Intent
   ↓
Command
   ↓
Execution Plan
   ↓
Approval / Decision Gates
   ↓
Plan Execution
   ↓
Operation Record
```

Commands generate Execution Plans.

Execution Plans are the executable artifacts.

Operation Records are the historical records of executed plans.

## Initial Scope

The full specification should define:

- Command responsibilities and lifecycle.
- Execution Plan structure.
- Plan validation and invalidation.
- Approval requirements.
- Decision Gate behavior.
- Plan execution behavior.
- Operation Record contents.
- Progress events.
- Cancellation behavior.
- Recovery and rollback hooks.
- Testing requirements.

## Non-Goals

Commands must not directly execute workflow steps.

UI components must not directly orchestrate service workflows.

Operation Records must not be treated as simple text logs.
