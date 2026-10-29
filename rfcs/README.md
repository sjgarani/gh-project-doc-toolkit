# Requests for Comments (RFCs)

Requests for Comments (RFCs) are formal technical proposals used to discuss, review, and align on major architectural changes, public APIs, infrastructural shifts, and large-scale features before writing code.

---

## When to Write an RFC vs. an ADR?

- **RFC (Request for Comments):** Proactive proposal for a major new capability, system architecture, or substantial refactoring. It invites debate on design trade-offs, alternative approaches, and implementation roadmaps.
- **ADR (Architecture Decision Record):** Captures a specific architectural decision that has been agreed upon, focusing on the context, forces, and immutable decision outcome.

Often, an accepted RFC leads to one or more focused ADRs capturing specific permanent architectural choices made during its implementation.

---

## File Structure & Naming Conventions

RFCs are stored in this directory following the pattern:
```
RFC-<number>-<short-slug>.md
```
Examples:
- `RFC-0001-microservice-event-protocol.md`
- `RFC-0002-zero-downtime-migration-strategy.md`

Files in this folder:
- `README.md`: This guide.
- `template.md`: Baseline template for creating new RFC proposals.
- `workflow.md`: Specification of lifecycle states and GitHub tools mapping.

---

## How to Work with RFCs

### 1. Creating a New RFC
```bash
./tools/doc-toolkit new rfc "Microservice Event Protocol" --author "@sjgarani"
```
This allocates the next sequence number (e.g. `RFC-0001`), generates the document from `template.md`, and sets the initial state to `DRAFT`.

### 2. Submitting for Team Review (GitHub PR)
1. Push your branch to GitHub.
2. Open a Pull Request for team review.
3. Link the RFC to the Pull Request:
   ```bash
   ./tools/doc-toolkit link rfcs/RFC-0001-microservice-event-protocol.md --pr 42
   ```
4. Move status to `REVIEW`:
   ```bash
   ./tools/doc-toolkit transition rfcs/RFC-0001-microservice-event-protocol.md REVIEW --actor "@sjgarani" --notes "Opened RFC PR #42 for team feedback"
   ```

### 3. Acceptance & Implementation
Once consensus is reached and the RFC PR is approved and merged:
```bash
./tools/doc-toolkit transition rfcs/RFC-0001-microservice-event-protocol.md ACCEPTED --actor "@tech-lead" --notes "Consensus reached; RFC merged"
```

Link tracking issues and implementation PRs:
```bash
./tools/doc-toolkit link rfcs/RFC-0001-microservice-event-protocol.md --issue 105
```

When code implementation is completed and deployed:
```bash
./tools/doc-toolkit transition rfcs/RFC-0001-microservice-event-protocol.md IMPLEMENTED --actor "@tech-lead" --notes "Feature shipped to production"
```

### 4. Viewing Status & History
```bash
# Matrix view of RFCs
./tools/doc-toolkit matrix --type rfc

# Full individual view and history audit trail
./tools/doc-toolkit status RFC-0001
```
