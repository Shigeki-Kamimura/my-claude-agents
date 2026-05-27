# NestJS Review Notes

Use this file when convergence tickets touch NestJS backend boundaries.

## Read In Order

1. controller or route decorator
2. DTO or schema validation
3. guard or auth decorator when relevant
4. service method receiving the request
5. nearest tests covering the contract

## Review Reminders

- Guard placement in the controller does not replace service-side ownership checks.
- DTO optionality must match what the service and caller actually expect.
- Validation changes are contract changes; require explicit verification evidence.
- Exception mapping should preserve intended user-visible behavior and avoid silent broad catches.

## Typical Merge Risks

- route param or body mismatch after a fix
- missing validation for newly accepted data
- service behavior depending on unchecked controller assumptions
- auth checks implemented only in the frontend or decorator layer
