# Architecture Decision Records (ADRs)

Architecture Decision Records (ADRs) capture significant architectural choices, context, trade-offs, and consequences made throughout the evolution of the software system.

---

## Why ADRs?

- **Preserve Institutional Memory:** Prevents "why did we do this?" debates months or years later.
- **Transparent Decision-Making:** Engages the entire engineering team in reviewing architectural changes.
- **Traceability with Git and GitHub:** Links technical discussions directly to Git commits and GitHub Pull Requests.

---

## File Structure & Naming Conventions

ADRs are stored in this directory following the pattern:
```
ADR-<number>-<short-slug>.md
```
Examples:
- `ADR-0001-record-architecture-decisions.md`
- `ADR-0002-adopt-postgresql-database.md`

Files in this folder:
- `README.md`: This guide.
- `template.md`: Baseline template for creating new records.
- `workflow.md`: Specification of the lifecycle states and transition rules.

---

## How to Work with ADRs

### 1. Creating a New ADR
Use the `doc-toolkit` CLI:
```bash
# In the project root or doc directory
./tools/doc-toolkit new adr "Adopt PostgreSQL Database"
```
This automatically allocates the next sequential number (e.g. `ADR-0002`), creates the file from `template.md`, populates the initial metadata block, and logs the creation in the history table.

### 2. Drafting and Reviewing
1. Edit the generated markdown file to fill in the **Context**, **Considered Options**, and **Decision Outcome**.
2. Push your branch to GitHub.
3. Link the ADR with a GitHub Pull Request:
   ```bash
   ./tools/doc-toolkit link adrs/ADR-0002-adopt-postgresql-database.md --pr 42
   ```
4. Move status to `PROPOSED`:
   ```bash
   ./tools/doc-toolkit transition adrs/ADR-0002-adopt-postgresql-database.md PROPOSED --actor "@developer" --notes "PR #42 opened for team review"
   ```

### 3. Acceptance or Rejection
Once the GitHub PR is approved and merged:
```bash
./tools/doc-toolkit transition adrs/ADR-0002-adopt-postgresql-database.md ACCEPTED --actor "@tech-lead" --notes "Merged PR #42"
```

If the proposal is rejected or abandoned:
```bash
./tools/doc-toolkit transition adrs/ADR-0002-adopt-postgresql-database.md REJECTED --actor "@tech-lead" --notes "PR #42 closed; latency requirements not met"
```

### 4. Viewing Status & History
View all ADRs in a matrix or list view:
```bash
# Matrix view of document lifecycle
./tools/doc-toolkit matrix --type adr

# Detailed status and history of an individual ADR
./tools/doc-toolkit status adrs/ADR-0002-adopt-postgresql-database.md
```

---

## Best Practices
1. **Immutable Once Accepted:** Once an ADR is marked `ACCEPTED`, its decision section is immutable. If circumstances change, propose a new ADR that supersedes the old one.
2. **Never Edit Toolkit Comments Manually:** Use `./tools/doc-toolkit` commands to perform state transitions and updates to ensure audit trails and history consistency.
