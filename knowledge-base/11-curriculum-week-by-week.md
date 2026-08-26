---
title: Week By Week Curriculum
category: Program
id: DOC-PG-001
---

# Week By Week Curriculum

## Shape Of The Program
One month, full time, for beginner computer science students. Three architectures are
built in sequence, each one motivated by a limitation of the previous one.

## Week 1: RAG End To End With TF-IDF
Install Foundry Local. Run the Node.js reference application unchanged and see a
complete RAG system working within the first day. Then replace its documents with your
own, rewrite the system prompt, and tune chunk size and topK.

Retrieval here is TF-IDF. No embedding model is involved. The learning goal is the
shape of the whole pipeline: ingest, chunk, index, retrieve, augment, generate.

Milestone: a working offline assistant answering questions about the student's own
documents.

## Week 2: Embeddings And Semantic Search
Switch to Python and the Microsoft Learn tutorial. Load a real embedding model, embed
a small in-memory document list, and implement cosine similarity and top-k selection
by hand.

The motivating question from week 1: why did TF-IDF miss a question that used
different words for the same idea? Embeddings are the answer.

Milestone: a command line assistant using genuine semantic retrieval.

## Week 3: Persistence And A Real Pipeline
Extend week 2 with file loading, paragraph-aware chunking, and a SQLite table holding
chunks and their vectors. Startup loads vectors from disk instead of re-embedding.

The retrieval function from week 2 is reused unchanged. Only the data source changes.
Recognising that boundary is the main architectural lesson of the week.

Milestone: an assistant that indexes once and starts instantly thereafter.

## Week 4: Interface, Testing, And Polish
Replace the command line with a Streamlit chat interface. Display the retrieved chunks
in the interface so retrieval quality is visible. Write test questions, including
questions the knowledge base cannot answer. Measure response times.

Milestone: a demonstrable application with documentation.

## Week 5: Evaluation, Documentation, Presentation
Systematic testing, tuning, a written report, and a demo. The demo should include
switching off the network to prove the offline claim.

## Sequencing Note
Weeks 1 and 2 use different retrieval architectures from different sources. Keeping
that distinction explicit prevents the confusion of expecting embedding content in the
TF-IDF material.
