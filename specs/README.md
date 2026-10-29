# Technical Specifications (SPECs)

Technical Specifications (SPECs) define functional requirements, acceptance criteria, API contracts, and testing strategies for features, subsystems, or bug investigations before implementation begins.

---

## Why Technical Specifications?

Code moves faster and has fewer regressions when acceptance criteria and edge cases are clearly defined and reviewed beforehand. Checking SPECs into Git ensures they evolve with the code and serve as living contracts.

---

## File Structure & Naming Conventions

Specification documents are stored in this directory following the pattern:
```
SPEC-<number>-<short-slug>.md
```
Examples:
- `SPEC-0001-rate-limiting-engine.md`
- `SPEC-0002-user-session-invalidation.md`

Files in this folder:
- `README.md`: This guide.
- `template.md`: Baseline template for creating new specifications.
- `workflow.md`: Specification of lifecycle states and GitHub tools mapping.

---

## How to Work with Specifications

### 1. Creating a New SPEC
```bash
./tools/doc-toolkit new spec "Rate Limiting Engine" --author "@sjgarani"
```
This allocates the next sequence number (e.g. `SPEC-0001`), generates the document from `template.md`, and sets the initial state to `DRAFT`.

### 2. Linking to GitHub Tools
- Link to a tracking GitHub Issue:
  ```bash
  ./tools/doc-toolkit link specs/SPEC-0001-rate-limiting-engine.md --issue 78
  ```
- Link to a delivery GitHub Pull Request:
  ```bash
  ./tools/doc-toolkit link specs/SPEC-0001-rate-limiting-engine.md --pr 95
  ```

### 3. Transitioning the Workflow
```bash
# Move to REVIEW
./tools/doc-toolkit transition specs/SPEC-0001-rate-limiting-engine.md REVIEW --actor "@sjgarani" --notes "Submitted for product sign-off"

# Move to APPROVED
./tools/doc-toolkit transition specs/SPEC-0001-rate-limiting-engine.md APPROVED --actor "@lead" --notes "Acceptance criteria approved"

# Move to IN_PROGRESS
./tools/doc-toolkit transition specs/SPEC-0001-rate-limiting-engine.md IN_PROGRESS --actor "@dev" --notes "Started work on Issue #78"

# Move to RESOLVED
./tools/doc-toolkit transition specs/SPEC-0001-rate-limiting-engine.md RESOLVED --actor "@dev" --pr 95 --notes "Delivered and verified via PR #95"
```

### 4. Viewing Status & History
```bash
# Matrix view of all specifications
./tools/doc-toolkit matrix --type spec

# Full status and audit history
./tools/doc-toolkit status SPEC-0001
```
