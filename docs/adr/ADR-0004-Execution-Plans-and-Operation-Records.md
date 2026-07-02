# ADR-0004 --- Execution Plans and Operation Records

**Status:** Accepted

**Date:** 2026-07-02

------------------------------------------------------------------------

# Context

Alchemist exists to help users safely build and maintain high-quality
audiobook libraries. Most meaningful user actions are not single
operations but workflows involving validation, metadata resolution, file
operations, external systems, and recovery.

Traditional applications execute actions directly. As workflows become
more complex, this approach obscures intent, complicates testing, and
makes it difficult to explain or recover from failures.

Alchemist adopts explicit execution planning as the foundation for
workflow execution.

------------------------------------------------------------------------

# Decision

Execution Plans are first-class architectural objects.

Commands translate user intent into Execution Plans.

Execution Plans are reviewed, approved when required, executed, and
finally preserved as Operation Records.

------------------------------------------------------------------------

# Architectural Principles

## 1. Commands Express Intent

Commands represent user intent.

A Command is responsible for validating inputs and producing an
Execution Plan.

Commands are workflow generators rather than workflow executors.

------------------------------------------------------------------------

## 2. Execution Plans Are the Executable Artifact

Execution Plans are independent objects that may be:

-   generated
-   displayed
-   approved
-   serialized
-   logged
-   tested
-   executed
-   audited

Future interfaces, including graphical, command-line, and automated
pipelines, execute the same Execution Plan model.

------------------------------------------------------------------------

## 3. Plans Describe Work Explicitly

An Execution Plan describes:

-   purpose
-   inputs
-   expected outputs
-   execution steps
-   validation results
-   warnings and risks
-   external systems involved
-   recovery information
-   approval requirements

Plans exist to explain work before it occurs.

------------------------------------------------------------------------

## 4. Plans Are Immutable After Approval

Once approved, an Execution Plan becomes immutable.

If the execution environment changes in a way that could affect
outcomes, the approved plan must be invalidated.

A new plan is generated and, when required, presented for approval.

Users must never approve one plan while the application silently
executes another.

------------------------------------------------------------------------

## 5. Decision Gates

Execution Plans may contain Decision Gates where human judgment is
required.

Execution pauses until the required decision is made.

Automation may continue through user-defined rules but must stop at
Decision Gates unless explicit policy permits continuation.

------------------------------------------------------------------------

## 6. Operation Records

An Operation Record is the historical record of an executed Execution
Plan.

It preserves:

-   the approved plan
-   execution timestamps
-   completed steps
-   warnings
-   errors
-   user decisions
-   recovery information
-   final outcome

Operation Records provide traceability rather than merely logging
events.

------------------------------------------------------------------------

## 7. Dry Runs

A dry run consists of generating and validating an Execution Plan
without executing it.

The same planning process must be used for both dry runs and real
execution.

------------------------------------------------------------------------

## 8. Recovery

Execution Plans should identify recovery opportunities whenever
practical.

Where recovery is impossible, plans should communicate that risk before
execution.

------------------------------------------------------------------------

## 9. Explainability

Every significant action performed by Alchemist should be explainable
through its Execution Plan and resulting Operation Record.

The application should never surprise the user with hidden actions.

------------------------------------------------------------------------

# Rationale

Separating intent, planning, execution, and historical recording creates
workflows that are safer, easier to test, easier to automate, and easier
to explain.

Execution Plans become the common language shared by graphical
interfaces, future CLI tools, automation pipelines, and operation
history.

------------------------------------------------------------------------

# Alternatives Considered

## Direct Command Execution

Rejected because execution becomes tightly coupled to individual
interfaces and is harder to inspect, test, serialize, or reuse.

## UI-Driven Workflows

Rejected because workflow orchestration should not live in presentation
code.

## Implicit Execution

Rejected because users should understand significant operations before
they occur.

------------------------------------------------------------------------

# Consequences

This decision establishes that:

-   Commands generate plans.
-   Plans execute.
-   Executed plans become Operation Records.
-   Automation operates through plans.
-   CLI, GUI, and future interfaces share the same execution model.
-   Environment changes invalidate approved plans.

------------------------------------------------------------------------

# Out of Scope

This ADR does not define:

-   command implementation
-   plan serialization format
-   pipeline engine
-   rollback implementation
-   progress event model
-   cancellation behavior

These are defined in subsystem specifications.

------------------------------------------------------------------------

# References

-   ADR-0001 --- Architectural Foundation
-   ADR-0002 --- Canonical Metadata and Metadata Resolution
-   ADR-0003 --- Identity Strategy
-   1000 --- System Architecture Specification
-   9000 --- Command Framework Specification (future)

------------------------------------------------------------------------

# Final Principle

Alchemist does not execute actions blindly.

It executes approved plans.

Every significant workflow should be understandable before execution,
predictable during execution, and fully explainable after execution.
