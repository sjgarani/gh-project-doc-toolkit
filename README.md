# gh-project-doc-toolkit

[![CLI Tests](https://img.shields.io/badge/tests-passing-brightgreen)]()
[![Zero Dependencies](https://img.shields.io/badge/dependencies-standard--library-blue)]()
[![Git Subtree Ready](https://img.shields.io/badge/git-subtree--ready-orange)]()

**gh-project-doc-toolkit** is a modular, zero-dependency documentation framework and workflow management toolkit designed to be imported into any Git repository as a **Git Subtree** (typically inside the `doc/` directory).

It standardizes and automates:
- **Architecture Decision Records (ADRs):** Records irreversible architectural decisions, trade-offs, and outcomes.
- **Requests for Comments (RFCs):** Proactive technical design proposals, RFC review, and consensus tracking.
- **Technical Specifications (SPECs):** Requirements, user stories, acceptance criteria, and API contracts.
- **Document-First GitHub Mapping:** Documents are the core versioned artifacts, mapping out to GitHub tools (Pull Requests for review/implementation, Issues for task tracking and milestones).
- **Managed Metadata & Audit History Blocks:** In Markdown via standard HTML comment tags.
- **Interactive Status Visualizations:** Dedicated matrix views per document type without redundant type columns, plus individual document status and full audit logs.
- **CLI Automation Engine** (`tools/doc-toolkit`): With workflow state validation and GitHub tool synchronization.

---

## Table of Contents

1. [How It Works as a Git Subtree](#1-how-it-works-as-a-git-subtree)
2. [Directory Structure](#2-directory-structure)
3. [Document Types & Workflows](#3-document-types--workflows)
4. [Mapping Document Types to GitHub Tools](#4-mapping-document-types-to-github-tools)
5. [Toolkit-Managed Comments & History](#5-toolkit-managed-comments--history)
6. [CLI Tool Usage & Reference](#6-cli-tool-usage--reference)
7. [Status Matrix & Visualizations](#7-status-matrix--visualizations)
8. [Running Tests](#8-running-tests)

---

## 1. How It Works as a Git Subtree

This repository is designed to live as a git subtree within a parent project under the `doc/` folder.

### Adding the Toolkit to a Parent Project
In your main repository:
```bash
git subtree add --prefix doc https://github.com/sjgarani/gh-project-doc-toolkit.git main --squash
```

### Initializing the Toolkit in the Parent Project
```bash
./doc/tools/doc-toolkit init --repo "your-org/your-repo"
```
The toolkit automatically detects whether it is running from the root of this toolkit repository or inside `doc/` within a parent repository.

### Pulling Upstream Updates
```bash
git subtree pull --prefix doc https://github.com/sjgarani/gh-project-doc-toolkit.git main --squash
```

---

## 2. Directory Structure

```
.
├── README.md               # Main toolkit documentation (this file)
├── doc-toolkit.json        # Toolkit configuration (GitHub repo, workflows, types)
├── adrs/                   # Architecture Decision Records
│   ├── README.md           # ADR user guide and best practices
│   ├── template.md         # ADR template with managed metadata and history
│   └── workflow.md         # ADR state machine and PR review rules
├── rfcs/                   # Requests for Comments (Technical Proposals)
│   ├── README.md           # RFC user guide and proposal best practices
│   ├── template.md         # RFC proposal template
│   └── workflow.md         # RFC state machine and consensus rules
├── specs/                  # Technical Specifications (Requirements & Contracts)
│   ├── README.md           # SPEC user guide and acceptance criteria format
│   ├── template.md         # Technical specification template
│   └── workflow.md         # SPEC state machine and delivery rules
└── tools/                  # Automation engine
    ├── doc-toolkit         # Executable CLI launcher
    ├── doc_toolkit.py      # Core Python 3 standard-library CLI implementation
    └── test_doc_toolkit.py # Automated test suite
```

---

## 3. Document Types & Workflows

Following software documentation industry best practices, documents are structured around technical change management (not GitHub tool names). Each document type is the source of truth that maps out to GitHub tools (PRs, Issues, Discussions).

### Architecture Decision Records (`adrs/`)
- **Purpose:** Capture architectural choices, drivers, considered options, trade-offs, and outcomes.
- **Statuses:** `DRAFT` ➔ `PROPOSED` ➔ `ACCEPTED` | `REJECTED` | `SUPERSEDED` | `DEPRECATED`
- **GitHub Tools Mapping:** Transition to `PROPOSED` pairs with an active GitHub Pull Request for architectural review. Merging the PR marks the ADR `ACCEPTED`.
- Read more: [adrs/README.md](adrs/README.md) and [adrs/workflow.md](adrs/workflow.md).

### Requests for Comments (`rfcs/`)
- **Purpose:** Formal technical proposals for major architectural changes, cross-cutting features, or system redesigns.
- **Statuses:** `DRAFT` ➔ `REVIEW` ➔ `ACCEPTED` ➔ `IMPLEMENTED` | `REJECTED` | `WITHDRAWN` | `SUPERSEDED`
- **GitHub Tools Mapping:** The RFC file is reviewed via a GitHub Pull Request (or Discussion). Once merged (`ACCEPTED`), its implementation tasks are tracked in GitHub Issues and delivered via feature PRs (`IMPLEMENTED`).
- Read more: [rfcs/README.md](rfcs/README.md) and [rfcs/workflow.md](rfcs/workflow.md).

### Technical Specifications (`specs/`)
- **Purpose:** Define requirements, user stories, BDD acceptance criteria (Given/When/Then), API contracts, and test plans.
- **Statuses:** `DRAFT` ➔ `REVIEW` ➔ `APPROVED` ➔ `IN_PROGRESS` ➔ `RESOLVED` ➔ `CLOSED`
- **GitHub Tools Mapping:** Binds to tracking GitHub Issues (for sprint planning / milestones) and delivery GitHub Pull Requests (delivering code and verifying acceptance criteria).
- Read more: [specs/README.md](specs/README.md) and [specs/workflow.md](specs/workflow.md).

---

## 4. Mapping Document Types to GitHub Tools

This toolkit adopts a **Document-First Architecture**: version-controlled Markdown documents are the single source of truth, and GitHub tools serve as the collaboration, review, and execution channels.

| Document Type | Document Lifecycle Stage | Mapped GitHub Tool | GitHub Action / State | Impact on Document |
| :--- | :--- | :--- | :--- | :--- |
| **ADR** | `PROPOSED` | **GitHub Pull Request** | Open PR labeled `adr` | Stakeholders review and approve architectural decision |
| **ADR** | `ACCEPTED` | **GitHub Pull Request** | PR merged into `main` | Status locks as `ACCEPTED`; merge logged in audit history |
| **ADR** | `REJECTED` | **GitHub Pull Request** | PR closed without merge | Status marked `REJECTED`; rationale preserved |
| **RFC** | `REVIEW` | **GitHub Pull Request** | Open PR labeled `rfc` | Formal RFC review, RFC line suggestions, debate |
| **RFC** | `ACCEPTED` | **GitHub Pull Request** | PR merged into `main` | Consensus approved; implementation tasks created |
| **RFC** | `IMPLEMENTED` | **GitHub Issues & PRs** | Milestone issues & PRs merged | Feature code delivered to production |
| **SPEC** | `REVIEW` / `APPROVED` | **GitHub Issue / Project** | Issue prioritized on Project Board | Requirements and BDD acceptance criteria signed off |
| **SPEC** | `IN_PROGRESS` | **GitHub Issue** | Assigned Issue labeled `in-progress` | Active development underway |
| **SPEC** | `RESOLVED` / `CLOSED` | **GitHub Pull Request(s)** | Delivery PR(s) merged | Acceptance criteria verified; shipped |

> [!TIP]
> For in-depth diagrams, lifecycle transition rules, and sequence flows, see the dedicated [GITHUB_MAPPING.md](GITHUB_MAPPING.md) guide.

---

## 5. Toolkit-Managed Comments & History

To prevent manual editing mistakes and maintain a reliable audit trail, documents contain standardized HTML comment markers. Human content is written in Markdown outside these blocks, while the tool maintains the metadata and history.

```markdown
<!-- ===================================================================== -->
<!-- TOOLKIT:MANAGED_START -->
<!--
TOOLKIT:METADATA
id: ADR-0001
type: adr
title: Record Architecture Decisions
status: PROPOSED
created_at: 2026-10-29T02:00:46Z
updated_at: 2026-10-29T02:02:52Z
authors: ["@sjgarani"]
github_repo: sjgarani/gh-project-doc-toolkit
github_pr: 1
github_issue: null
-->
<!-- ===================================================================== -->

## Status

**Status:** `PROPOSED`  
**Date:** 2026-10-29  
**Associated GitHub PR:** #1  
**Associated GitHub Issue:** Not linked  

<!-- ===================================================================== -->
<!-- TOOLKIT:HISTORY_START -->
## History

| Timestamp (UTC) | From Status | To Status | Actor | Notes / PR Reference |
| :--- | :--- | :--- | :--- | :--- |
| 2026-10-29 02:00 | - | DRAFT | @sjgarani | Initial ADR created |
| 2026-10-29 02:02 | DRAFT | PROPOSED | @sjgarani | Opened PR #1 for team review (PR #1) |
<!-- TOOLKIT:HISTORY_END -->
<!-- TOOLKIT:MANAGED_END -->
<!-- ===================================================================== -->
```

> [!NOTE]
> When executing `./tools/doc-toolkit transition` or `./tools/doc-toolkit link`, the tool automatically parses and updates the `TOOLKIT:METADATA`, refreshes the Markdown `## Status` snippet, and appends an audit entry to `## History`.

---

## 6. CLI Tool Usage & Reference

The CLI is located at `./tools/doc-toolkit` (or `./doc/tools/doc-toolkit` if used as subtree). It is completely dependency-free, running on standard Python 3.8+.

### Commands

#### 1. Initialize Configuration
```bash
./tools/doc-toolkit init --repo "owner/repo"
```

#### 2. Create a New Document
Automatically assigns the next sequence number (e.g. `ADR-0002`, `RFC-0001`, `SPEC-0001`), generates the file from `template.md`, sets the initial status, and logs the creation in History:
```bash
# New ADR (Architecture Decision Record)
./tools/doc-toolkit new adr "Adopt PostgreSQL Database" --author "@sjgarani"

# New RFC (Technical Proposal / Design Document)
./tools/doc-toolkit new rfc "Microservice Event Protocol" --author "@sjgarani"

# New SPEC (Technical Specification / Requirements)
./tools/doc-toolkit new spec "Public API Rate Limiting" --author "@sjgarani"
```

#### 3. View Document Status
```bash
# List all documents in summary table
./tools/doc-toolkit status

# Filter by document type
./tools/doc-toolkit status --type adr
./tools/doc-toolkit status --type rfc
./tools/doc-toolkit status --type spec

# Detailed individual document view (metadata, next allowed transitions, full history)
./tools/doc-toolkit status RFC-0001
```

#### 4. Matrix Status View (Rows = Docs, Columns = Statuses)
```bash
# Matrix view of active statuses (separated by type, without Type column)
./tools/doc-toolkit matrix

# Matrix view of a specific document type
./tools/doc-toolkit matrix --type adr
./tools/doc-toolkit matrix --type rfc
./tools/doc-toolkit matrix --type spec
```

#### 5. Transition Document Workflow State
Transitions are validated against the state machine defined in `workflow.md`:
```bash
# Transition ADR to PROPOSED and associate with review PR #42
./tools/doc-toolkit transition ADR-0001 PROPOSED --pr 42 --actor "@sjgarani" --notes "Opened PR #42"

# Transition RFC to REVIEW and associate with RFC PR #10
./tools/doc-toolkit transition RFC-0001 REVIEW --pr 10 --actor "@sjgarani" --notes "Opened RFC PR #10"

# Transition to ACCEPTED once merged
./tools/doc-toolkit transition ADR-0001 ACCEPTED --actor "@techlead" --notes "Merged PR #42"

# Emergency override (maintainers only)
./tools/doc-toolkit transition ADR-0001 DRAFT --force --notes "Reopened for amendments"
```

#### 6. Link GitHub Pull Request or Issue
```bash
./tools/doc-toolkit link ADR-0001 --pr 42
./tools/doc-toolkit link SPEC-0001 --issue 78 --pr 95
```

#### 7. View History Audit Trail
```bash
./tools/doc-toolkit history ADR-0001
```

#### 8. Validate Documents
Validates all documents against their respective schemas, required comments, and valid workflow states:
```bash
./tools/doc-toolkit validate
```

#### 9. GitHub CLI Synchronization
Queries `gh` CLI (if installed and authenticated) to check whether associated PRs/Issues are open, merged, or closed:
```bash
./tools/doc-toolkit sync
```

---

## 7. Status Matrix & Visualizations

### Matrix View (`./tools/doc-toolkit matrix`)
Visualizes status across all document types, cleanly separated into dedicated sections without a redundant "Type" column:

```
=== Architecture Decision Record (ADR) ===
+------------------------------------------+-------+----------+----------+----------+----------+--------+
| Document                                 | DRAFT | PROPOSED | ACCEPTED | REJECTED | SUPERSED | DEPREC |
+------------------------------------------+-------+----------+----------+----------+----------+--------+
| ADR-0001 (Record Architecture Decisions) | ·     | [● #1]   | ·        | ·        | ·        | ·      |
+------------------------------------------+-------+----------+----------+----------+----------+--------+

=== Pull Request Specification (PR) ===
+-----------------------------------------------+-------+-----------+-------------+----------+--------+--------+
| Document                                      | DRAFT | IN_REVIEW | CHANGES_REQ | APPROVED | MERGED | CLOSED |
+-----------------------------------------------+-------+-----------+-------------+----------+--------+--------+
| PR-0001 (Initialize Git Subtree Documenta...) | [●]   | ·         | ·           | ·        | ·      | ·      |
+-----------------------------------------------+-------+-----------+-------------+----------+--------+--------+

=== Issue Specification (ISSUE) ===
+--------------------------------------------------+---------+---------+---------+---------+--------+--------+
| Document                                         | BACKLOG | TRIAGED | IN_PROG | BLOCKED | RESOLV | CLOSED |
+--------------------------------------------------+---------+---------+---------+---------+--------+--------+
| ISSUE-0001 (Provide GitHub Actions Integrati...) | [●]     | ·       | ·       | ·       | ·      | ·      |
+--------------------------------------------------+---------+---------+---------+---------+--------+--------+
```

### Type-Specific Matrix (`./tools/doc-toolkit matrix --type adr`)
```
=== Architecture Decision Record (ADR) ===
+------------------------------------------+-------+----------+----------+----------+----------+--------+
| Document                                 | DRAFT | PROPOSED | ACCEPTED | REJECTED | SUPERSED | DEPREC |
+------------------------------------------+-------+----------+----------+----------+----------+--------+
| ADR-0001 (Record Architecture Decisions) | ·     | [● #1]   | ·        | ·        | ·        | ·      |
+------------------------------------------+-------+----------+----------+----------+----------+--------+
```

### Individual Document View (`./tools/doc-toolkit status ADR-0001`)
```
======================================================================
 DOCUMENT: ADR-0001 - Record Architecture Decisions
======================================================================
  Type:                ADR (Architecture Decision Record)
  Current Status:      PROPOSED
  File Path:           adrs/ADR-0001-record-architecture-decisions.md
  Created At:          2026-10-29T02:00:46Z
  Updated At:          2026-10-29T02:02:52Z
  GitHub Repo:         sjgarani/gh-project-doc-toolkit
  GitHub PR:           #1
  GitHub Issue:        Not linked
  Authors:             @sjgarani
  Allowed Transitions: ACCEPTED, REJECTED, DRAFT
----------------------------------------------------------------------
 HISTORY & AUDIT TRAIL:
----------------------------------------------------------------------
+------------------+-------+----------+-----------+--------------------------------------+
| Timestamp (UTC)  | From  | To       | Actor     | Notes / Reference                    |
+------------------+-------+----------+-----------+--------------------------------------+
| 2026-10-29 02:00 | -     | DRAFT    | @sjgarani | Initial ADR created                  |
| 2026-10-29 02:02 | DRAFT | PROPOSED | @sjgarani | Opened PR #1 for team review (PR #1) |
+------------------+-------+----------+-----------+--------------------------------------+
======================================================================
```

---

## 8. Running Tests

The test suite runs with standard `unittest` and requires no third-party libraries:

```bash
python3 -m unittest tools/test_doc_toolkit.py
```
