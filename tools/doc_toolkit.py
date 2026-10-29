#!/usr/bin/env python3
"""
gh-project-doc-toolkit - CLI Document and Workflow Management Tool

Manages Architecture Decision Records (ADRs), Pull Request (PR) specifications,
and Issue documentation with GitHub association, workflow state validation,
managed metadata comment blocks, chronological audit history, and matrix status views.
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Default configuration
DEFAULT_CONFIG = {
    "version": "1.0.0",
    "github_repo": "",
    "doc_root": ".",
    "types": {
        "adr": {
            "name": "Architecture Decision Record",
            "dir": "adrs",
            "prefix": "ADR",
            "digits": 4,
            "template": "adrs/template.md",
            "workflow": "adrs/workflow.md",
            "statuses": [
                "DRAFT",
                "PROPOSED",
                "ACCEPTED",
                "REJECTED",
                "SUPERSEDED",
                "DEPRECATED",
            ],
            "initial_status": "DRAFT",
            "transitions": {
                "DRAFT": ["PROPOSED", "REJECTED"],
                "PROPOSED": ["ACCEPTED", "REJECTED", "DRAFT"],
                "ACCEPTED": ["SUPERSEDED", "DEPRECATED"],
                "REJECTED": ["DRAFT", "PROPOSED"],
                "SUPERSEDED": [],
                "DEPRECATED": [],
            },
        },
        "rfc": {
            "name": "Request for Comments",
            "dir": "rfcs",
            "prefix": "RFC",
            "digits": 4,
            "template": "rfcs/template.md",
            "workflow": "rfcs/workflow.md",
            "statuses": [
                "DRAFT",
                "REVIEW",
                "ACCEPTED",
                "IMPLEMENTED",
                "REJECTED",
                "WITHDRAWN",
                "SUPERSEDED",
            ],
            "initial_status": "DRAFT",
            "transitions": {
                "DRAFT": ["REVIEW", "WITHDRAWN"],
                "REVIEW": ["ACCEPTED", "REJECTED", "WITHDRAWN", "DRAFT"],
                "ACCEPTED": ["IMPLEMENTED", "SUPERSEDED", "REJECTED"],
                "IMPLEMENTED": ["SUPERSEDED"],
                "REJECTED": ["DRAFT"],
                "WITHDRAWN": ["DRAFT"],
                "SUPERSEDED": [],
            },
        },
        "spec": {
            "name": "Technical Specification",
            "dir": "specs",
            "prefix": "SPEC",
            "digits": 4,
            "template": "specs/template.md",
            "workflow": "specs/workflow.md",
            "statuses": [
                "DRAFT",
                "REVIEW",
                "APPROVED",
                "IN_PROGRESS",
                "RESOLVED",
                "CLOSED",
            ],
            "initial_status": "DRAFT",
            "transitions": {
                "DRAFT": ["REVIEW", "CLOSED"],
                "REVIEW": ["APPROVED", "DRAFT", "CLOSED"],
                "APPROVED": ["IN_PROGRESS", "REVIEW", "CLOSED"],
                "IN_PROGRESS": ["RESOLVED", "APPROVED", "CLOSED"],
                "RESOLVED": ["CLOSED", "IN_PROGRESS"],
                "CLOSED": ["DRAFT", "REVIEW"],
            },
        },
    },
}

CONFIG_FILENAMES = ["doc-toolkit.json", ".doc-toolkit.json"]


class ToolkitManager:
    def __init__(self, explicit_root: Optional[str] = None):
        self.root_dir = self._detect_toolkit_root(explicit_root)
        self.config_path, self.config = self._load_config()

    def _detect_toolkit_root(self, explicit_root: Optional[str]) -> Path:
        """
        Locates the documentation root. Supports:
        1. Explicit path given via CLI or environment variable DOC_TOOLKIT_DIR.
        2. Current working directory if adrs/ exists.
        3. doc/ directory if running from the root of a parent repository where
           gh-project-doc-toolkit is used as a git subtree.
        4. Parent directory if run directly from inside tools/.
        """
        if explicit_root:
            p = Path(explicit_root).resolve()
            if p.exists():
                return p

        env_root = os.environ.get("DOC_TOOLKIT_DIR")
        if env_root:
            p = Path(env_root).resolve()
            if p.exists():
                return p

        cwd = Path.cwd().resolve()
        # Case A: inside the toolkit itself
        if (cwd / "adrs").is_dir() and ((cwd / "rfcs").is_dir() or (cwd / "specs").is_dir()):
            return cwd

        # Case B: inside parent repository with doc/ subtree
        if (cwd / "doc" / "adrs").is_dir():
            return cwd / "doc"

        # Case C: script is located in tools/, check its parent
        script_dir = Path(__file__).resolve().parent
        parent = script_dir.parent
        if (parent / "adrs").is_dir():
            return parent

        # Fallback to current working directory
        return cwd

    def _load_config(self) -> Tuple[Path, Dict[str, Any]]:
        for fname in CONFIG_FILENAMES:
            p = self.root_dir / fname
            if p.is_file():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    cfg = DEFAULT_CONFIG.copy()
                    cfg.update(data)
                    return p, cfg
                except Exception:
                    pass

        # Return default config path in root
        default_path = self.root_dir / "doc-toolkit.json"
        return default_path, DEFAULT_CONFIG.copy()

    def save_config(self) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)
            f.write("\n")

    def get_github_repo(self) -> str:
        repo = self.config.get("github_repo")
        if repo:
            return repo

        # Attempt to auto-detect from git remote
        try:
            res = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=str(self.root_dir),
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                url = res.stdout.strip()
                # Match github.com:owner/repo.git or https://github.com/owner/repo.git
                m = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)", url)
                if m:
                    return f"{m.group('owner')}/{m.group('repo')}"
        except Exception:
            pass
        return ""

    def list_documents(self, doc_type: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        types_to_check = [doc_type] if doc_type else list(self.config["types"].keys())

        for t in types_to_check:
            t_info = self.config["types"].get(t)
            if not t_info:
                continue
            dir_path = self.root_dir / t_info["dir"]
            if not dir_path.is_dir():
                continue

            for f in sorted(dir_path.glob("*.md")):
                if f.name.lower() in ["readme.md", "template.md", "workflow.md"]:
                    continue
                doc = self.parse_document(f)
                if doc:
                    results.append(doc)

        return results

    def parse_document(self, file_path: Path) -> Optional[Dict[str, Any]]:
        if not file_path.is_file():
            return None

        content = file_path.read_text(encoding="utf-8")

        # Parse TOOLKIT:MANAGED comment block
        managed_pattern = re.compile(
            r"<!--\s*TOOLKIT:MANAGED_START\s*-->"
            r"(.*?)"
            r"<!--\s*TOOLKIT:MANAGED_END\s*-->",
            re.DOTALL,
        )
        managed_match = managed_pattern.search(content)

        # Parse METADATA block
        metadata = {}
        meta_pattern = re.compile(
            r"<!--\s*TOOLKIT:METADATA\s*(.*?)\s*-->", re.DOTALL
        )
        meta_match = meta_pattern.search(content)
        if meta_match:
            meta_lines = meta_match.group(1).strip().splitlines()
            for line in meta_lines:
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip()
                    # Parse json-like values (lists, numbers, strings, null)
                    if val.startswith("[") and val.endswith("]"):
                        try:
                            metadata[key] = json.loads(val)
                        except Exception:
                            metadata[key] = [
                                x.strip().strip('"\'')
                                for x in val[1:-1].split(",")
                                if x.strip()
                            ]
                    elif val.isdigit():
                        metadata[key] = int(val)
                    elif val.lower() == "null":
                        metadata[key] = None
                    elif val.lower() == "true":
                        metadata[key] = True
                    elif val.lower() == "false":
                        metadata[key] = False
                    else:
                        metadata[key] = val.strip('"\'')

        # Fallback doc_id and type from filename if missing
        file_name = file_path.name
        doc_id = metadata.get("id")
        if not doc_id:
            m = re.match(r"^([A-Z]+-\d+)", file_name)
            doc_id = m.group(1) if m else file_name

        doc_type = metadata.get("type")
        if not doc_type:
            prefix = doc_id.split("-")[0].lower() if "-" in doc_id else ""
            for k, v in self.config["types"].items():
                if v["prefix"].lower() == prefix:
                    doc_type = k
                    break
            if not doc_type:
                doc_type = "adr"

        # Parse title from H1 or metadata
        title = metadata.get("title")
        if not title:
            h1_match = re.search(r"^#\s+(?:\[[^\]]+\]\s*)?(.*)$", content, re.MULTILINE)
            title = h1_match.group(1).strip() if h1_match else file_path.stem

        # Parse history entries
        history_entries = []
        hist_pattern = re.compile(
            r"<!--\s*TOOLKIT:HISTORY_START\s*-->"
            r"(.*?)"
            r"<!--\s*TOOLKIT:HISTORY_END\s*-->",
            re.DOTALL,
        )
        hist_match = hist_pattern.search(content)
        if hist_match:
            lines = hist_match.group(1).strip().splitlines()
            for line in lines:
                line_str = line.strip()
                if line_str.startswith("|") and not line_str.startswith("| :---"):
                    cols = [c.strip() for c in line_str.strip("|").split("|")]
                    if len(cols) >= 5 and cols[0] != "Timestamp (UTC)":
                        history_entries.append(
                            {
                                "timestamp": cols[0],
                                "from_status": cols[1],
                                "to_status": cols[2],
                                "actor": cols[3],
                                "notes": cols[4],
                            }
                        )

        status = metadata.get("status", "UNKNOWN")

        return {
            "id": doc_id,
            "type": doc_type,
            "title": title,
            "status": status.upper(),
            "path": file_path,
            "rel_path": str(file_path.relative_to(self.root_dir)),
            "metadata": metadata,
            "history": history_entries,
            "raw_content": content,
        }

    def find_document(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Finds a document by ID (e.g. ADR-0001), relative path, or filename.
        """
        # Direct path check
        p = Path(identifier)
        if not p.is_absolute():
            p = self.root_dir / identifier
        if p.is_file():
            return self.parse_document(p)

        all_docs = self.list_documents()
        norm_id = identifier.strip().upper()

        for doc in all_docs:
            if doc["id"].upper() == norm_id:
                return doc
            if Path(doc["rel_path"]).name.upper() == norm_id:
                return doc
            if norm_id in doc["id"].upper():
                return doc

        return None

    def create_document(
        self,
        doc_type: str,
        title: str,
        author: Optional[str] = None,
        github_pr: Optional[int] = None,
        github_issue: Optional[int] = None,
    ) -> Path:
        doc_type = doc_type.lower()
        if doc_type not in self.config["types"]:
            raise ValueError(
                f"Unknown document type '{doc_type}'. Allowed types: {list(self.config['types'].keys())}"
            )

        t_info = self.config["types"][doc_type]
        target_dir = self.root_dir / t_info["dir"]
        target_dir.mkdir(parents=True, exist_ok=True)

        template_path = self.root_dir / t_info["template"]
        if not template_path.is_file():
            raise FileNotFoundError(f"Template not found at {template_path}")

        template_content = template_path.read_text(encoding="utf-8")

        # Determine next ID
        existing_docs = self.list_documents(doc_type)
        max_num = 0
        prefix = t_info["prefix"]
        for d in existing_docs:
            m = re.match(rf"^{prefix}-(\d+)", d["id"])
            if m:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num

        next_num = max_num + 1
        num_str = str(next_num).zfill(t_info["digits"])
        doc_id = f"{prefix}-{num_str}"

        # Generate slug
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
        if not slug:
            slug = "document"
        filename = f"{doc_id}-{slug}.md"
        target_file = target_dir / filename

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        iso_now = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        display_date = now_utc.strftime("%Y-%m-%d")
        display_time = now_utc.strftime("%Y-%m-%d %H:%M")

        repo_name = self.get_github_repo()
        initial_status = t_info["initial_status"]
        actor_name = author or os.environ.get("USER", "system")

        # Replace placeholders in template
        new_content = template_content
        new_content = re.sub(
            r"\[" + prefix + r"-0000\][^\n]*",
            f"[{doc_id}] {title}",
            new_content,
            count=1,
        )

        metadata_dict = {
            "id": doc_id,
            "type": doc_type,
            "title": title,
            "status": initial_status,
            "created_at": iso_now,
            "updated_at": iso_now,
            "authors": [actor_name] if actor_name else [],
            "github_repo": repo_name,
            "github_pr": github_pr,
            "github_issue": github_issue,
        }

        # Build metadata text
        meta_lines = ["<!--", "TOOLKIT:METADATA"]
        for k, v in metadata_dict.items():
            if v is None:
                meta_lines.append(f"{k}: null")
            elif isinstance(v, (list, dict)):
                meta_lines.append(f"{k}: {json.dumps(v)}")
            else:
                meta_lines.append(f"{k}: {v}")
        meta_lines.append("-->")
        meta_text = "\n".join(meta_lines)

        # Build initial status block
        pr_link_text = f"#{github_pr}" if github_pr else "Not linked"
        issue_link_text = f"#{github_issue}" if github_issue else "Not linked"
        status_block = (
            f"## Status\n\n"
            f"**Status:** `{initial_status}`  \n"
            f"**Date:** {display_date}  \n"
            f"**Associated GitHub PR:** {pr_link_text}  \n"
            f"**Associated GitHub Issue:** {issue_link_text}  \n"
        )

        # Build initial history table
        history_block = (
            f"<!-- TOOLKIT:HISTORY_START -->\n"
            f"## History\n\n"
            f"| Timestamp (UTC) | From Status | To Status | Actor | Notes / PR Reference |\n"
            f"| :--- | :--- | :--- | :--- | :--- |\n"
            f"| {display_time} | - | {initial_status} | {actor_name} | Initial {doc_type.upper()} created |\n"
            f"<!-- TOOLKIT:HISTORY_END -->"
        )

        # Replace managed section
        managed_body = (
            f"<!-- ===================================================================== -->\n"
            f"<!-- TOOLKIT:MANAGED_START -->\n"
            f"{meta_text}\n"
            f"<!-- ===================================================================== -->\n\n"
            f"{status_block}\n"
            f"<!-- ===================================================================== -->\n"
            f"{history_block}\n"
            f"<!-- TOOLKIT:MANAGED_END -->\n"
            f"<!-- ===================================================================== -->"
        )

        # Substitute managed section in template if present
        if "<!-- TOOLKIT:MANAGED_START -->" in new_content:
            new_content = re.sub(
                r"<!-- ===================================================================== -->\s*"
                r"<!--\s*TOOLKIT:MANAGED_START\s*-->.*?"
                r"<!--\s*TOOLKIT:MANAGED_END\s*-->\s*"
                r"<!-- ===================================================================== -->",
                managed_body,
                new_content,
                flags=re.DOTALL,
            )
        else:
            # Insert after the title H1
            new_content = re.sub(
                r"(^#[^\n]+\n)", r"\1\n" + managed_body + "\n\n", new_content, count=1
            )

        target_file.write_text(new_content, encoding="utf-8")
        return target_file

    def transition_document(
        self,
        doc: Dict[str, Any],
        new_status: str,
        actor: Optional[str] = None,
        notes: Optional[str] = None,
        github_pr: Optional[int] = None,
        github_issue: Optional[int] = None,
        force: bool = False,
    ) -> bool:
        doc_type = doc["type"]
        current_status = doc["status"].upper()
        target_status = new_status.strip().upper()

        t_info = self.config["types"].get(doc_type, {})
        allowed_statuses = t_info.get("statuses", [])
        transitions = t_info.get("transitions", {})

        if target_status not in allowed_statuses and not force:
            raise ValueError(
                f"Invalid status '{target_status}' for {doc_type}. Allowed: {allowed_statuses}"
            )

        valid_next = transitions.get(current_status, [])
        if not force and target_status not in valid_next and target_status != current_status:
            raise ValueError(
                f"Illegal transition from '{current_status}' to '{target_status}'. "
                f"Allowed transitions from {current_status}: {valid_next}"
            )

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        iso_now = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        display_date = now_utc.strftime("%Y-%m-%d")
        display_time = now_utc.strftime("%Y-%m-%d %H:%M")
        actor_name = actor or os.environ.get("USER", "system")

        metadata = doc["metadata"].copy()
        metadata["status"] = target_status
        metadata["updated_at"] = iso_now
        if github_pr is not None:
            metadata["github_pr"] = github_pr
        if github_issue is not None:
            metadata["github_issue"] = github_issue

        content = doc["raw_content"]

        # Build updated metadata string
        meta_lines = ["<!--", "TOOLKIT:METADATA"]
        for k, v in metadata.items():
            if v is None:
                meta_lines.append(f"{k}: null")
            elif isinstance(v, (list, dict)):
                meta_lines.append(f"{k}: {json.dumps(v)}")
            else:
                meta_lines.append(f"{k}: {v}")
        meta_lines.append("-->")
        new_meta_text = "\n".join(meta_lines)

        content = re.sub(
            r"<!--\s*TOOLKIT:METADATA\s*.*?-->",
            new_meta_text,
            content,
            flags=re.DOTALL,
        )

        # Update ## Status block
        pr_val = metadata.get("github_pr")
        issue_val = metadata.get("github_issue")
        pr_display = f"#{pr_val}" if pr_val else "Not linked"
        issue_display = f"#{issue_val}" if issue_val else "Not linked"

        new_status_block = (
            f"## Status\n\n"
            f"**Status:** `{target_status}`  \n"
            f"**Date:** {display_date}  \n"
            f"**Associated GitHub PR:** {pr_display}  \n"
            f"**Associated GitHub Issue:** {issue_display}  \n"
        )

        status_pattern = re.compile(
            r"## Status\s*\n\s*\*\*Status:\*\*.*?(?=(<!--|##|\Z))", re.DOTALL
        )
        if status_pattern.search(content):
            content = status_pattern.sub(new_status_block, content, count=1)

        # Update History table
        note_str = notes or f"Transitioned from {current_status} to {target_status}"
        if github_pr:
            note_str += f" (PR #{github_pr})"
        new_row = f"| {display_time} | {current_status} | {target_status} | {actor_name} | {note_str} |"

        hist_pattern = re.compile(
            r"(<!--\s*TOOLKIT:HISTORY_START\s*-->.*?"
            r"\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\s*:---\s*\|\n)"
            r"(.*?)"
            r"(<!--\s*TOOLKIT:HISTORY_END\s*-->)",
            re.DOTALL,
        )
        hist_match = hist_pattern.search(content)
        if hist_match:
            header_part = hist_match.group(1)
            rows_part = hist_match.group(2)
            end_part = hist_match.group(3)
            # Append new row
            updated_rows = rows_part.rstrip() + "\n" + new_row + "\n"
            content = (
                content[: hist_match.start()]
                + header_part
                + updated_rows
                + end_part
                + content[hist_match.end() :]
            )

        doc["path"].write_text(content, encoding="utf-8")
        return True

    def link_github(
        self,
        doc: Dict[str, Any],
        github_pr: Optional[int] = None,
        github_issue: Optional[int] = None,
        actor: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        actor_name = actor or os.environ.get("USER", "system")
        current_status = doc["status"]
        note_text = notes or "Linked GitHub references"
        if github_pr:
            note_text += f" [PR #{github_pr}]"
        if github_issue:
            note_text += f" [Issue #{github_issue}]"

        return self.transition_document(
            doc=doc,
            new_status=current_status,
            actor=actor_name,
            notes=note_text,
            github_pr=github_pr,
            github_issue=github_issue,
            force=True,
        )

    def validate_all(self) -> List[Dict[str, Any]]:
        docs = self.list_documents()
        errors = []

        for d in docs:
            doc_type = d["type"]
            t_info = self.config["types"].get(doc_type)
            if not t_info:
                errors.append(
                    {
                        "doc": d["id"],
                        "file": d["rel_path"],
                        "error": f"Unknown document type '{doc_type}'",
                    }
                )
                continue

            if d["status"] not in t_info["statuses"]:
                errors.append(
                    {
                        "doc": d["id"],
                        "file": d["rel_path"],
                        "error": f"Status '{d['status']}' not in allowed statuses {t_info['statuses']}",
                    }
                )

            # Check if comments are present
            raw = d["raw_content"]
            if not re.search(r"<!--\s*TOOLKIT:METADATA", raw):
                errors.append(
                    {
                        "doc": d["id"],
                        "file": d["rel_path"],
                        "error": "Missing '<!-- TOOLKIT:METADATA' comment block",
                    }
                )
            if not re.search(r"<!--\s*TOOLKIT:HISTORY_START\s*-->", raw):
                errors.append(
                    {
                        "doc": d["id"],
                        "file": d["rel_path"],
                        "error": "Missing '<!-- TOOLKIT:HISTORY_START -->' comment block",
                    }
                )

        return errors


# =============================================================================
# CLI Formatting Helpers
# =============================================================================

def format_table(headers: List[str], rows: List[List[str]]) -> str:
    """Renders a clean ASCII/Unicode terminal table with aligned columns."""
    if not rows:
        return "(no records found)"

    widths = [len(h) for h in headers]
    for row in rows:
        for idx, col in enumerate(row):
            widths[idx] = max(widths[idx], len(str(col)))

    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    header_line = "| " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)) + " |"

    lines = [sep, header_line, sep]
    for row in rows:
        row_line = (
            "| "
            + " | ".join(str(c).ljust(w) for c, w in zip(row, widths))
            + " |"
        )
        lines.append(row_line)
    lines.append(sep)
    return "\n".join(lines)


def render_single_type_matrix(
    docs: List[Dict[str, Any]],
    type_key: str,
    type_info: Dict[str, Any],
) -> str:
    """Renders the matrix table for a single document type without a Type column."""
    statuses = type_info.get("statuses", [])
    abbrev_map = {
        "CHANGES_REQUESTED": "CHANGES_REQ",
        "IN_PROGRESS": "IN_PROG",
        "SUPERSEDED": "SUPERSED",
        "DEPRECATED": "DEPREC",
        "RESOLVED": "RESOLV",
    }
    col_headers = [abbrev_map.get(s, s) for s in statuses]
    headers = ["Document"] + col_headers

    if not docs:
        return "  (no documents registered)"

    rows = []
    for d in docs:
        label = (
            f"{d['id']} ({d['title'][:32]}...)"
            if len(d["title"]) > 32
            else f"{d['id']} ({d['title']})"
        )
        row = [label]
        for s in statuses:
            if d["status"] == s:
                pr = d["metadata"].get("github_pr")
                if pr:
                    row.append(f"[● #{pr}]")
                else:
                    row.append("[●]")
            else:
                row.append("·")
        rows.append(row)

    return format_table(headers, rows)


def render_matrix_view(
    docs: List[Dict[str, Any]],
    doc_type: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    all_statuses: bool = False,
) -> str:
    """
    Renders the matrix view:
    - Separated by document type (ADR, PR, Issue)
    - Rows: documents (ID & Title)
    - Columns: workflow statuses for that specific type
    - NO 'Type' column
    """
    if not docs:
        return "No documents found."

    cfg = config or DEFAULT_CONFIG

    if doc_type:
        t_key = doc_type.lower()
        t_info = cfg["types"].get(t_key)
        if not t_info:
            return f"Unknown document type: '{doc_type}'"
        type_docs = [d for d in docs if d["type"].lower() == t_key]
        header = f"=== {t_info.get('name', t_key.upper())} ({t_info.get('prefix', t_key.upper())}) ==="
        return f"{header}\n{render_single_type_matrix(type_docs, t_key, t_info)}"

    # When displaying all: separate sections for each type without 'Type' column
    sections = []
    for t_key, t_info in cfg["types"].items():
        type_docs = [d for d in docs if d["type"].lower() == t_key]
        header = f"=== {t_info.get('name', t_key.upper())} ({t_info.get('prefix', t_key.upper())}) ==="
        table = render_single_type_matrix(type_docs, t_key, t_info)
        sections.append(f"{header}\n{table}")

    return "\n\n".join(sections)


def render_individual_view(doc: Dict[str, Any], manager: ToolkitManager) -> str:
    """Renders a detailed view of a single document."""
    meta = doc["metadata"]
    t_info = manager.config["types"].get(doc["type"], {})
    valid_next = t_info.get("transitions", {}).get(doc["status"], [])

    lines = [
        "=" * 70,
        f" DOCUMENT: {doc['id']} - {doc['title']}",
        "=" * 70,
        f"  Type:                {doc['type'].upper()} ({t_info.get('name', '')})",
        f"  Current Status:      {doc['status']}",
        f"  File Path:           {doc['rel_path']}",
        f"  Created At:          {meta.get('created_at', 'N/A')}",
        f"  Updated At:          {meta.get('updated_at', 'N/A')}",
        f"  GitHub Repo:         {meta.get('github_repo') or manager.get_github_repo() or 'Not configured'}",
        f"  GitHub PR:           #{meta.get('github_pr')}" if meta.get("github_pr") else "  GitHub PR:           Not linked",
        f"  GitHub Issue:        #{meta.get('github_issue')}" if meta.get("github_issue") else "  GitHub Issue:        Not linked",
        f"  Authors:             {', '.join(meta.get('authors', [])) or 'None'}",
        f"  Allowed Transitions: {', '.join(valid_next) if valid_next else '(terminal state)'}",
        "-" * 70,
        " HISTORY & AUDIT TRAIL:",
        "-" * 70,
    ]

    hist_rows = []
    for h in doc.get("history", []):
        hist_rows.append(
            [
                h.get("timestamp", ""),
                h.get("from_status", ""),
                h.get("to_status", ""),
                h.get("actor", ""),
                h.get("notes", ""),
            ]
        )

    if hist_rows:
        lines.append(
            format_table(
                ["Timestamp (UTC)", "From", "To", "Actor", "Notes / Reference"],
                hist_rows,
            )
        )
    else:
        lines.append("  (no history recorded)")

    lines.append("=" * 70)
    return "\n".join(lines)


# =============================================================================
# Main CLI Dispatcher
# =============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="doc-toolkit",
        description="gh-project-doc-toolkit: Manage ADRs, PR specs, and Issues with GitHub workflows.",
    )
    parser.add_argument(
        "--root",
        help="Path to documentation root (auto-detected if omitted).",
        default=None,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: init
    cmd_init = subparsers.add_parser("init", help="Initialize or update toolkit configuration.")
    cmd_init.add_argument("--repo", help="GitHub repository in 'owner/repo' format.")

    # Command: new
    cmd_new = subparsers.add_parser("new", help="Create a new document from template.")
    cmd_new.add_argument("type", choices=["adr", "rfc", "spec"], help="Document type.")
    cmd_new.add_argument("title", help="Title or subject of the document.")
    cmd_new.add_argument("--author", help="Author handle or name.")
    cmd_new.add_argument("--pr", type=int, help="Optional initial GitHub PR number.")
    cmd_new.add_argument("--issue", type=int, help="Optional initial GitHub Issue number.")

    # Command: status
    cmd_status = subparsers.add_parser("status", help="View status of documents.")
    cmd_status.add_argument(
        "target",
        nargs="?",
        default=None,
        help="Optional Document ID or path for individual view.",
    )
    cmd_status.add_argument("--type", choices=["adr", "rfc", "spec"], help="Filter by type.")
    cmd_status.add_argument(
        "--matrix",
        action="store_true",
        help="Display status matrix (rows=documents, cols=statuses).",
    )
    cmd_status.add_argument(
        "-a",
        "--all-statuses",
        action="store_true",
        help="Include all defined workflow statuses as columns in matrix view.",
    )

    # Command: matrix
    cmd_matrix = subparsers.add_parser(
        "matrix", help="Display matrix view (rows=documents, cols=statuses)."
    )
    cmd_matrix.add_argument("--type", choices=["adr", "rfc", "spec"], help="Filter by type.")
    cmd_matrix.add_argument(
        "-a",
        "--all-statuses",
        action="store_true",
        help="Include all defined workflow statuses as columns in matrix view.",
    )

    # Command: transition
    cmd_trans = subparsers.add_parser("transition", help="Transition document workflow state.")
    cmd_trans.add_argument("target", help="Document ID (e.g. ADR-0001) or file path.")
    cmd_trans.add_argument("status", help="Target status.")
    cmd_trans.add_argument("--actor", help="Actor or user executing the transition.")
    cmd_trans.add_argument("--notes", help="Audit notes / reason for transition.")
    cmd_trans.add_argument("--pr", type=int, help="Associated GitHub PR number.")
    cmd_trans.add_argument("--issue", type=int, help="Associated GitHub Issue number.")
    cmd_trans.add_argument(
        "--force",
        action="store_true",
        help="Bypass workflow transition rules (maintainers only).",
    )

    # Command: link
    cmd_link = subparsers.add_parser(
        "link", help="Link a document to a GitHub Pull Request or Issue."
    )
    cmd_link.add_argument("target", help="Document ID or file path.")
    cmd_link.add_argument("--pr", type=int, help="GitHub Pull Request number.")
    cmd_link.add_argument("--issue", type=int, help="GitHub Issue number.")
    cmd_link.add_argument("--notes", help="Audit notes.")

    # Command: history
    cmd_hist = subparsers.add_parser("history", help="Show chronological audit history of a document.")
    cmd_hist.add_argument("target", help="Document ID or file path.")

    # Command: validate
    cmd_val = subparsers.add_parser("validate", help="Validate all documents against workflow specifications.")

    # Command: sync
    cmd_sync = subparsers.add_parser(
        "sync", help="Check/sync document status with GitHub PR/Issue via gh CLI."
    )
    cmd_sync.add_argument("target", nargs="?", help="Optional specific document ID or file path.")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    manager = ToolkitManager(explicit_root=args.root)

    # Handler: init
    if args.command == "init":
        repo = args.repo or manager.get_github_repo()
        manager.config["github_repo"] = repo
        manager.save_config()
        print(f"Toolkit initialized at: {manager.root_dir}")
        print(f"Config file: {manager.config_path}")
        print(f"GitHub Repository: {repo or '(not set - use --repo owner/repo)'}")
        return 0

    # Handler: new
    if args.command == "new":
        try:
            created_path = manager.create_document(
                doc_type=args.type,
                title=args.title,
                author=args.author,
                github_pr=args.pr,
                github_issue=args.issue,
            )
            rel = created_path.relative_to(manager.root_dir)
            print(f"Created new {args.type.upper()}: {rel}")
            print(f"View details: ./tools/doc-toolkit status {rel}")
            return 0
        except Exception as e:
            print(f"Error creating document: {e}", file=sys.stderr)
            return 1

    # Handler: status / matrix
    if args.command in ["status", "matrix"]:
        is_matrix = args.command == "matrix" or getattr(args, "matrix", False)
        target = getattr(args, "target", None)
        doc_filter = getattr(args, "type", None)

        # If a specific target document is requested
        if target:
            doc = manager.find_document(target)
            if not doc:
                print(f"Error: Document '{target}' not found.", file=sys.stderr)
                return 1
            print(render_individual_view(doc, manager))
            return 0

        # Collect list of documents
        docs = manager.list_documents(doc_filter)

        if is_matrix:
            all_cols = getattr(args, "all_statuses", False)
            print(render_matrix_view(docs, doc_type=doc_filter, config=manager.config, all_statuses=all_cols))
            return 0

        # Standard summary table view
        headers = ["ID", "Type", "Title", "Status", "GitHub PR", "GitHub Issue", "Updated"]
        rows = []
        for d in docs:
            pr = f"#{d['metadata'].get('github_pr')}" if d['metadata'].get("github_pr") else "-"
            iss = f"#{d['metadata'].get('github_issue')}" if d['metadata'].get("github_issue") else "-"
            upd = d["metadata"].get("updated_at", "")[:10]
            rows.append(
                [
                    d["id"],
                    d["type"].upper(),
                    d["title"][:32],
                    d["status"],
                    pr,
                    iss,
                    upd,
                ]
            )
        print(format_table(headers, rows))
        return 0

    # Handler: transition
    if args.command == "transition":
        doc = manager.find_document(args.target)
        if not doc:
            print(f"Error: Document '{args.target}' not found.", file=sys.stderr)
            return 1

        try:
            manager.transition_document(
                doc=doc,
                new_status=args.status,
                actor=args.actor,
                notes=args.notes,
                github_pr=args.pr,
                github_issue=args.issue,
                force=args.force,
            )
            print(f"Transitioned {doc['id']} to {args.status.upper()}")
            return 0
        except Exception as e:
            print(f"Transition Error: {e}", file=sys.stderr)
            return 1

    # Handler: link
    if args.command == "link":
        doc = manager.find_document(args.target)
        if not doc:
            print(f"Error: Document '{args.target}' not found.", file=sys.stderr)
            return 1

        if not args.pr and not args.issue:
            print("Error: Specify at least one of --pr <number> or --issue <number>.", file=sys.stderr)
            return 1

        manager.link_github(
            doc=doc,
            github_pr=args.pr,
            github_issue=args.issue,
            notes=args.notes,
        )
        print(f"Updated GitHub links for {doc['id']}")
        return 0

    # Handler: history
    if args.command == "history":
        doc = manager.find_document(args.target)
        if not doc:
            print(f"Error: Document '{args.target}' not found.", file=sys.stderr)
            return 1

        hist = doc.get("history", [])
        if not hist:
            print(f"No history recorded for {doc['id']}.")
            return 0

        rows = [
            [
                h.get("timestamp", ""),
                h.get("from_status", ""),
                h.get("to_status", ""),
                h.get("actor", ""),
                h.get("notes", ""),
            ]
            for h in hist
        ]
        print(f"History for {doc['id']} ({doc['title']}):")
        print(format_table(["Timestamp (UTC)", "From", "To", "Actor", "Notes / Reference"], rows))
        return 0

    # Handler: validate
    if args.command == "validate":
        errors = manager.validate_all()
        if not errors:
            print("All documents passed validation! No schema or workflow errors found.")
            return 0
        else:
            print(f"Found {len(errors)} validation error(s):", file=sys.stderr)
            for err in errors:
                print(f" - [{err['doc']}] {err['file']}: {err['error']}", file=sys.stderr)
            return 1

    # Handler: sync
    if args.command == "sync":
        repo = manager.get_github_repo()
        if not repo:
            print("Notice: GitHub repo not configured. Run './tools/doc-toolkit init --repo owner/repo'")
            return 0

        docs = [manager.find_document(args.target)] if args.target else manager.list_documents()
        docs = [d for d in docs if d]

        print(f"Syncing with GitHub repository: {repo}")
        synced = 0
        for d in docs:
            pr_num = d["metadata"].get("github_pr")
            if pr_num:
                # Try gh pr view
                try:
                    res = subprocess.run(
                        ["gh", "pr", "view", str(pr_num), "--repo", repo, "--json", "state,mergedAt"],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if res.returncode == 0:
                        pr_data = json.loads(res.stdout)
                        pr_state = pr_data.get("state") # OPEN, MERGED, CLOSED
                        print(f" - {d['id']}: PR #{pr_num} state is {pr_state}")
                        synced += 1
                except Exception:
                    pass

        print(f"Sync check completed for {synced} linked documents.")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
