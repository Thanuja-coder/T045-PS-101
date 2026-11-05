# T045 – PS-101 Decision Log

Record each design or implementation decision with its date, reason, affected business rule, and whether it is confirmed or provisional.

| ID | Date | Decision / question | Reason | Affected rule(s) | Status |
|---|---|---|---|---|---|
| D-001 | 2026-11-05 | Use Python 3.10+ for the implementation. | Python is one of the two permitted languages and supports the required file processing, date calculations and testing. | All | Confirmed |
| D-002 | 2026-11-05 | Build a command-file-driven application with no frontend. | The problem statement explicitly requires no UI. | All | Confirmed |
| D-003 | 2026-11-05 | Begin with in-memory domain records; decide persistence only if the supplied input/output specification requires it. | The brief specifies command files and reports, not a database. | All | Provisional |
| D-004 | 2026-11-05 | Keep unresolved business-rule boundaries isolated until the coordinator clarifies them. | Avoid silently choosing behaviour that may differ from hidden expected outputs. | BR-07, BR-08, BR-09, BR-11 | Provisional |
| D-005 | 2026-11-05 | Prefer Python standard-library modules and `unittest` initially. | Reduce setup overhead and keep the implementation easy to explain. | All | Confirmed |
| D-006 | 2026-11-05 | Use `Decimal` for monetary calculations. | Avoid binary floating-point rounding issues in rupee calculations. | BR-04, BR-08, BR-11 | Planned |
| D-007 | 2026-11-05 | Model carried-forward and current-cycle credits as distinguishable ledger lots/transactions so FIFO and expiry can be applied. | Required to consume older credits first and expire carry-forward at the correct cycle boundary. | BR-05 | Planned |

## Template for future entries

| ID | Date | Decision / question | Reason | Affected rule(s) | Status |
|---|---|---|---|---|---|
| D-___ | YYYY-MM-DD |  |  |  | Provisional / Confirmed |

**Status meanings**
- Confirmed: explicitly stated in the problem brief or confirmed by the coordinator.
- Planned: intended implementation approach, not yet verified in code.
- Provisional: temporary interpretation awaiting clarification.
- Replaced: superseded by a later decision; retain the old entry for traceability.

