# SPEC_TEMPLATE.md

---
spec:
  id: SPEC-XXXX
  title: "<Feature Name>"
  version: 1.0
  status: Draft | Architecture Review | Approved | Implementation | Code Review | Verified | Frozen | Deprecated
  priority: Critical | High | Medium | Low

owner: Project Architect
reviewer: Project Architect
implementer: Claude Code

created:
last_updated:

depends_on:
required_by:

estimated_complexity:
estimated_effort:
---

# SPEC-XXXX — <Feature Name>

---

## 🏛️ Boundary Validation Questions

Prior to architectural review and approval, the designer must document the answers to these five boundary validation questions:

1.  **Why does this module exist?**
    - *Answer*: [Explain the core problem this module solves and its necessity.]
2.  **Why is this the right boundary?**
    - *Answer*: [Define what lies inside and outside of this module's scope.]
3.  **Could another module own this responsibility?**
    - *Answer*: [Justify why this module must own this responsibility instead of existing modules.]
4.  **What happens if this module disappears?**
    - *Answer*: [Describe the cascading failures or architectural impacts of its absence.]
5.  **Will we still like this design in two years?**
    - *Answer*: [Detail the extensibility and durability of this structural choice.]

---

# 1. Executive Summary

Provide a concise overview of this module.

Answer:
- What is this module?
- Why does it exist?
- Why is it important?
- Why is it being built now?

Maximum length:
2–4 paragraphs.

---

# 2. Problem Statement

Describe the engineering problem this module solves.

Answer questions such as:
- What limitation currently exists?
- What risks occur if this module does not exist?
- Why can't another module solve this problem?

---

# 3. Objectives

Clearly define what this module MUST accomplish.

Example format:
- Objective 1
- Objective 2
- Objective 3

Objectives should be measurable.

---

# 4. Non-Objectives

Equally important.
List everything this module intentionally DOES NOT do.
This prevents feature creep.

Example:
This module will NOT:
- ...
- ...
- ...

---

# 5. Architectural Context

Explain where this module lives.

Include:
- Current Layer
- Department
- Related Components
- Neighbour Modules
- Information Flow

Example:
Presentation
↓
Planning
↓
This Module
↓
Execution

---

# 6. Responsibilities

List every responsibility.

Example:
The module SHALL
- ...
- ...
- ...

The module SHALL NOT
- ...
- ...
- ...

Single Responsibility Principle should be obvious here.

---

# 7. Functional Requirements

Describe every required capability.

- **FR-001**: Description | Priority: High | Acceptance: Verifiable metric.
- **FR-002**: ...

---

# 8. Non-Functional Requirements

Specify behavioral attributes:
- Performance
- Reliability
- Maintainability
- Security
- Scalability
- Extensibility
- Observability

---

# 9. Public Interfaces

Describe what other modules can access.
Include:
- Inputs
- Outputs
- Requests
- Responses
- Events

Do NOT write code. Describe contracts only.

---

# 10. Internal Components

Describe the internal conceptual pieces.

Example:
- Validator
- Loader
- Parser
- Cache

Responsibilities only. No implementation details.

---

# 11. Data Model

If the module owns data.
Describe:
- Entities
- Relationships
- Identifiers
- Lifecycle
- Ownership

No database schema yet.

---

# 12. Lifecycle

Describe module lifecycle.

Example:
Created -> Initialized -> Validated -> Ready -> Running -> Stopped -> Disposed

---

# 13. Event Model

Since SYNTHRA is event-driven.
List every event:
- **Event Name**: Producer | Consumer | Payload | Purpose

---

# 14. Error Handling

Describe expected failures.

Example:
- Missing configuration -> Fail Fast
- Network unavailable -> Retry
- Invalid state -> Abort
- Unexpected exception -> Bubble upward

Never swallow exceptions.

---

# 15. Logging Strategy

What should be logged?
- Startup
- Shutdown
- Warnings
- Errors
- Performance metrics
- Critical Events

Avoid logging sensitive data.

---

# 16. Security Considerations

Does this module:
- Access secrets?
- Access network?
- Access filesystem?
- Execute code?
- Manage permissions?

Explain boundaries.

---

# 17. Configuration Requirements

List every configurable behavior.
Do not specify format. Only describe configurable concepts.

---

# 18. Dependencies

- Internal dependencies
- External dependencies
- Dependency direction
Explain WHY.

---

# 19. Testing Strategy

Outline test categories:
- Unit Tests
- Integration Tests
- Failure Tests
- Boundary Tests

Testing philosophy, not implementation.

---

# 20. Acceptance Criteria

This is the contract. The SPEC is considered implemented only if:
✅ Item 1
✅ Item 2

---

# 21. Out of Scope

Explicitly list what will NOT be implemented. This section is mandatory.

---

# 22. Future Expansion

Possible future enhancements. These are NOT current requirements.

---

# 23. Risks

- **Risk**: Description | Impact: High | Mitigation: Strategy.

---

# 24. Alternatives Considered

Document other options and why they were rejected.

---

# 25. Open Questions

List unresolved questions.

---

# 26. References

- Architecture.md
- Constitution.md
- Relevant ADRs
- Relevant RFCs
- Relevant DESIGNs

---

# 27. Revision History

| Version | Date | Author | Summary |
|----------|------|---------|----------|
| 1.0 | | | Initial Draft |

---

# 28. Implementation Checklist

Before Implementation
☐ Reviewed
☐ Approved
☐ Dependencies Ready
☐ ADR Required?

Implementation
☐ Code Complete
☐ Tests Complete
☐ Documentation Updated
☐ Logging Verified
☐ Error Handling Verified

Post Implementation
☐ Reviewed
☐ Accepted
☐ Frozen

---

## Architect Notes

Free-form notes, engineering reasoning, trade-offs, and lessons learned.
