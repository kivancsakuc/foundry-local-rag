"""Tests for the parts of the pipeline that do not need a model loaded.

Run:  python -m unittest test_rag -v
"""

import tempfile
import unittest
from pathlib import Path

import config
import rag


class TestFrontMatter(unittest.TestCase):
    def test_parses_metadata_and_body(self):
        meta, body = rag.parse_front_matter(
            "---\ntitle: Hello\ncategory: Concepts\n---\n# Heading\n\nText."
        )
        self.assertEqual(meta["title"], "Hello")
        self.assertEqual(meta["category"], "Concepts")
        self.assertTrue(body.startswith("# Heading"))

    def test_document_without_front_matter_is_returned_whole(self):
        meta, body = rag.parse_front_matter("# Heading\n\nText.")
        self.assertEqual(meta, {})
        self.assertEqual(body, "# Heading\n\nText.")


class TestChunking(unittest.TestCase):
    def test_short_document_is_one_chunk(self):
        self.assertEqual(len(rag.chunk_text("one two three")), 1)

    def test_paragraphs_are_grouped_until_the_limit(self):
        para = " ".join(["word"] * 60)
        text = "\n\n".join([para] * 5)  # 300 words, limit 200
        chunks = rag.chunk_text(text, max_tokens=200, overlap_tokens=25)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk.split()), 200)

    def test_oversized_paragraph_is_windowed_with_overlap(self):
        words = [f"w{i}" for i in range(500)]
        chunks = rag.chunk_text(" ".join(words), max_tokens=100, overlap_tokens=20)
        self.assertGreater(len(chunks), 1)
        first, second = chunks[0].split(), chunks[1].split()
        self.assertEqual(first[-20:], second[:20], "chunks must overlap")

    def test_no_content_is_lost(self):
        words = [f"w{i}" for i in range(300)]
        chunks = rag.chunk_text(" ".join(words), max_tokens=100, overlap_tokens=20)
        seen = set()
        for chunk in chunks:
            seen.update(chunk.split())
        self.assertEqual(seen, set(words))

    def test_blank_input_produces_no_chunks(self):
        self.assertEqual(rag.chunk_text("   \n\n  "), [])


class TestCosineSimilarity(unittest.TestCase):
    def test_identical_vectors_score_one(self):
        self.assertAlmostEqual(rag.cosine_similarity([1, 2, 3], [1, 2, 3]), 1.0)

    def test_orthogonal_vectors_score_zero(self):
        self.assertAlmostEqual(rag.cosine_similarity([1, 0], [0, 1]), 0.0)

    def test_magnitude_is_ignored(self):
        self.assertAlmostEqual(rag.cosine_similarity([1, 1], [5, 5]), 1.0)

    def test_zero_vector_does_not_divide_by_zero(self):
        self.assertEqual(rag.cosine_similarity([0, 0], [1, 1]), 0.0)


class TestFindRelevant(unittest.TestCase):
    def test_ranks_by_similarity_and_respects_top_k(self):
        docs = [[1, 0], [0, 1], [0.9, 0.1]]
        results = rag.find_relevant([1, 0], docs, top_k=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][0], 0)
        self.assertEqual(results[1][0], 2)

    def test_top_k_larger_than_corpus_returns_everything(self):
        self.assertEqual(len(rag.find_relevant([1, 0], [[1, 0], [0, 1]], top_k=10)), 2)


class TestVectorStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.db"
        self.conn = rag.connect(self.db)

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_starts_empty(self):
        self.assertEqual(rag.count_chunks(self.conn), 0)

    def test_round_trips_a_vector_without_loss(self):
        vector = [0.1, -0.2, 0.30000000004]
        rag.insert_chunks(
            self.conn, [rag.Chunk("a.md", "A", "body text", vector)]
        )
        loaded = rag.load_chunks(self.conn)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].embedding, vector)
        self.assertEqual(loaded[0].source, "a.md")
        self.assertEqual(loaded[0].title, "A")

    def test_clear_removes_everything(self):
        rag.insert_chunks(self.conn, [rag.Chunk("a.md", "A", "x", [1.0])])
        rag.clear(self.conn)
        self.assertEqual(rag.count_chunks(self.conn), 0)

    def test_connect_creates_parent_directory(self):
        nested = Path(self.tmp.name) / "deep" / "nested" / "x.db"
        conn = rag.connect(nested)
        self.assertTrue(nested.exists())
        conn.close()


class TestPromptAssembly(unittest.TestCase):
    def test_context_and_question_are_in_separate_messages(self):
        chunks = [rag.Chunk("a.md", "Doc A", "alpha content", [1.0])]
        messages = rag.build_messages("what is alpha?", chunks)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("alpha content", messages[0]["content"])
        self.assertIn("Doc A", messages[0]["content"])
        self.assertEqual(messages[1], {"role": "user", "content": "what is alpha?"})

    def test_system_prompt_forbids_guessing(self):
        messages = rag.build_messages("q", [])
        self.assertIn("ONLY the context", messages[0]["content"])


class TestKnowledgeBase(unittest.TestCase):
    def test_shared_knowledge_base_exists_and_has_documents(self):
        self.assertTrue(config.DOCS_DIR.exists(), config.DOCS_DIR)
        self.assertGreater(len(list(config.DOCS_DIR.glob("*.md"))), 0)

    def test_every_document_chunks_to_something(self):
        for path in config.DOCS_DIR.glob("*.md"):
            _, body = rag.parse_front_matter(path.read_text(encoding="utf-8"))
            self.assertGreater(len(rag.chunk_text(body)), 0, path.name)


if __name__ == "__main__":
    unittest.main()
