#!/usr/bin/env python3
"""
Unit and integration tests for doc_toolkit.py
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add tools directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from doc_toolkit import ToolkitManager, render_matrix_view, render_individual_view, format_table


class TestDocToolkit(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory mimicking the repo structure
        self.test_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.test_dir.name)

        # Copy templates and workflows into temp directory
        src_root = Path(__file__).resolve().parent.parent
        for d in ["adrs", "rfcs", "specs"]:
            target_d = self.root / d
            target_d.mkdir(parents=True, exist_ok=True)
            for f in ["template.md", "workflow.md", "README.md"]:
                src_file = src_root / d / f
                if src_file.exists():
                    shutil.copy(src_file, target_d / f)

        self.manager = ToolkitManager(explicit_root=str(self.root))

    def tearDown(self):
        self.test_dir.cleanup()

    def test_init_config(self):
        self.manager.config["github_repo"] = "example-org/sample-repo"
        self.manager.save_config()

        # Reload manager
        reloaded = ToolkitManager(explicit_root=str(self.root))
        self.assertEqual(reloaded.get_github_repo(), "example-org/sample-repo")

    def test_create_and_parse_adr(self):
        created_file = self.manager.create_document(
            doc_type="adr",
            title="Adopt Event Sourcing",
            author="@architect",
            github_pr=101,
        )
        self.assertTrue(created_file.is_file())
        self.assertIn("ADR-0001", created_file.name)

        # Parse document
        doc = self.manager.find_document("ADR-0001")
        self.assertIsNotNone(doc)
        self.assertEqual(doc["id"], "ADR-0001")
        self.assertEqual(doc["type"], "adr")
        self.assertEqual(doc["title"], "Adopt Event Sourcing")
        self.assertEqual(doc["status"], "DRAFT")
        self.assertEqual(doc["metadata"]["github_pr"], 101)
        self.assertEqual(len(doc["history"]), 1)
        self.assertEqual(doc["history"][0]["to_status"], "DRAFT")

    def test_create_rfc_and_spec(self):
        rfc_file = self.manager.create_document(
            doc_type="rfc",
            title="Event-Driven Order Processing",
            author="@architect",
        )
        self.assertTrue(rfc_file.is_file())
        self.assertIn("RFC-0001", rfc_file.name)

        spec_file = self.manager.create_document(
            doc_type="spec",
            title="Public API Rate Limiting",
            author="@engineer",
        )
        self.assertTrue(spec_file.is_file())
        self.assertIn("SPEC-0001", spec_file.name)

        all_docs = self.manager.list_documents()
        ids = [d["id"] for d in all_docs]
        self.assertIn("RFC-0001", ids)
        self.assertIn("SPEC-0001", ids)

    def test_transitions_and_history(self):
        self.manager.create_document("adr", "Use GraphQL API")
        doc = self.manager.find_document("ADR-0001")

        # Legal transition: DRAFT -> PROPOSED
        self.manager.transition_document(
            doc=doc,
            new_status="PROPOSED",
            actor="@alice",
            notes="Submitted RFC for review",
            github_pr=55,
        )

        doc = self.manager.find_document("ADR-0001")
        self.assertEqual(doc["status"], "PROPOSED")
        self.assertEqual(doc["metadata"]["github_pr"], 55)
        self.assertEqual(len(doc["history"]), 2)
        self.assertEqual(doc["history"][1]["from_status"], "DRAFT")
        self.assertEqual(doc["history"][1]["to_status"], "PROPOSED")
        self.assertEqual(doc["history"][1]["actor"], "@alice")

        # Legal transition: PROPOSED -> ACCEPTED
        self.manager.transition_document(
            doc=doc,
            new_status="ACCEPTED",
            actor="@bob",
            notes="Consensus reached in architecture board",
        )
        doc = self.manager.find_document("ADR-0001")
        self.assertEqual(doc["status"], "ACCEPTED")
        self.assertEqual(len(doc["history"]), 3)

        # Illegal transition: ACCEPTED -> DRAFT (should fail without force)
        with self.assertRaises(ValueError):
            self.manager.transition_document(doc=doc, new_status="DRAFT")

        # Forced transition
        self.manager.transition_document(doc=doc, new_status="DRAFT", force=True)
        doc = self.manager.find_document("ADR-0001")
        self.assertEqual(doc["status"], "DRAFT")

    def test_matrix_and_table_rendering(self):
        self.manager.create_document("adr", "First Architecture Decision")
        self.manager.create_document("rfc", "First RFC Proposal")
        self.manager.create_document("spec", "First Specification")

        docs = self.manager.list_documents()
        self.assertEqual(len(docs), 3)

        # Render matrix view for all types (separated by type, without Type column)
        matrix_output = render_matrix_view(docs, config=self.manager.config)
        self.assertIn("Document", matrix_output)
        self.assertIn("ADR-0001", matrix_output)
        self.assertIn("RFC-0001", matrix_output)
        self.assertIn("SPEC-0001", matrix_output)
        self.assertIn("[●]", matrix_output)
        self.assertNotIn(" | Type | ", matrix_output)
        self.assertIn("=== Architecture Decision Record", matrix_output)
        self.assertIn("=== Request for Comments", matrix_output)
        self.assertIn("=== Technical Specification", matrix_output)

        # Render matrix for single type
        adr_output = render_matrix_view(docs, doc_type="adr", config=self.manager.config)
        self.assertIn("ADR-0001", adr_output)
        self.assertNotIn("RFC-0001", adr_output)
        self.assertNotIn(" | Type | ", adr_output)

        # Render individual view
        indiv_output = render_individual_view(docs[0], self.manager)
        self.assertIn("DOCUMENT: ADR-0001", indiv_output)
        self.assertIn("HISTORY & AUDIT TRAIL", indiv_output)

    def test_validation(self):
        self.manager.create_document("adr", "Valid ADR")
        errors = self.manager.validate_all()
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
