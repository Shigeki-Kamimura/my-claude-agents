## Ticket State Machine

All implementation and review work must be handled through explicit ticket states.
Agents must not skip states unless the user explicitly instructs them to do so.

### States

- Draft
  - Requirements or design notes are incomplete.
  - No implementation should start.

- Ready for PL
  - Requirements are available but need decomposition, constraints, or decision framing.
  - Responsible agent: PL.

- Ready for HQ
  - Implementation scope is defined.
  - Responsible agent: HQ.
  - HQ must implement the minimum safe delta required by the ticket.

- Ready for QA
  - Implementation is complete enough for L0/L1 verification.
  - Responsible agent: QA.

- Ready for L2+ Review
  - L0/L1 verification has passed or failures are explicitly documented.
  - Responsible agent: Adviser.

- Fix Required
  - Review findings require implementation changes.
  - Responsible agent: HQ.
  - HQ must fix only the reviewed scope unless follow-up work is explicitly approved.

- Convergence Review
  - Fixes have been applied.
  - Responsible agent: Adviser.
  - Review must focus on whether prior findings were resolved and whether regressions were introduced.

- Human Review
  - The work is ready for human review.
  - No agent should continue expanding the scope.

- Done
  - The ticket is completed and no further action is required.
