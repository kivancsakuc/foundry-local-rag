/**
 * Retrieval-only smoke test for the TF-IDF path. No chat model is loaded.
 *
 * The question set is identical to path-c-sqlite/retrieval_check.py, so the two
 * outputs can be read side by side. That comparison is the evidence for why the
 * curriculum moves from TF-IDF to embeddings.
 *
 * Usage: node retrieval_check.js
 */
import { config } from "./src/config.js";
import { VectorStore } from "./src/vectorStore.js";

// (question, exact title of the document that SHOULD be the top hit)
const CASES = [
  // Plainly worded - any retriever should get these.
  ["How do I install Foundry Local?", "What Is Foundry Local"],
  ["How large should a chunk be?", "Document Chunking Strategy"],
  ["How do I store vectors in a database?", "Storing Embeddings In SQLite"],
  // Worded differently from the source text - these separate semantic search
  // from keyword matching.
  ["The assistant keeps making things up. What do I do?",
   "Prompt Engineering For Grounded Question Answering"],
  ["Which model is fast enough for students to iterate with?",
   "Choosing A Local Chat Model"],
  ["Nothing happens when I run the CLI, it just sits there",
   "Troubleshooting Guide"],
];

const OUT_OF_SCOPE =
  "How many students fit in the lab, and what is the tuition fee?";

const store = new VectorStore(config.dbPath);
const total = store.count();

if (total === 0) {
  console.error("No chunks indexed. Run `npm run ingest` first.");
  process.exit(1);
}

console.log(`Loaded ${total} chunks (TF-IDF, no embedding model).\n`);

let passed = 0;

for (const [question, expected] of CASES) {
  const started = performance.now();
  const results = store.search(question, 3);
  const elapsed = performance.now() - started;

  const rank = results.findIndex((r) => r.title === expected);
  const ok = rank === 0;
  passed += ok ? 1 : 0;

  console.log(`${ok ? "PASS" : "MISS"}  ${question}`);
  console.log(`      expected "${expected}", top hit "${results[0]?.title}"`);
  if (rank > 0) {
    console.log(`      (expected document was ranked ${rank + 1} of 3)`);
  } else if (rank < 0) {
    console.log(`      (expected document was not in the top 3 at all)`);
  }
  results.forEach((r, i) => {
    console.log(`        ${i + 1}. ${r.score.toFixed(3)}  ${r.title}`);
  });
  console.log(`      retrieved in ${elapsed.toFixed(0)} ms\n`);
}

const oos = store.search(OUT_OF_SCOPE, 3);
console.log(`OUT OF SCOPE  ${OUT_OF_SCOPE}`);
console.log(
  `      best score ${oos[0] ? oos[0].score.toFixed(3) : "n/a"} ` +
    `(${oos[0] ? oos[0].title : "no hit"})\n`
);

console.log(
  `${passed}/${CASES.length} questions retrieved the expected document at rank 1.`
);
store.close();
