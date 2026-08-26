---
title: Retrieval-Augmented Generation Explained
category: Concepts
id: DOC-CN-001
---

# Retrieval-Augmented Generation Explained

## Summary
RAG is a design pattern with three steps: Retrieve relevant text from your own
document collection, Augment the model's prompt with that text, then Generate an
answer from the augmented prompt.

## The Problem RAG Solves
A language model only knows what was in its training data. Ask a small local model
about your company's internal maintenance procedure and it will either refuse or
invent something plausible. Neither is useful.

RAG fixes this without retraining anything. You keep the model as-is and change what
you put in front of it.

## The Three Steps

### 1. Retrieve
Given a user question, find the passages in your document collection that are most
likely to contain the answer. This is a search problem, not an AI problem. Two very
different techniques are covered in this program: TF-IDF keyword scoring and neural
embeddings.

### 2. Augment
Paste the retrieved passages into the prompt, usually in the system message, with an
instruction telling the model to answer only from that context.

### 3. Generate
Call the model. Because the answer is grounded in supplied text, hallucination drops
sharply and you can cite sources.

## Benefits
- Answers reflect your data, not the model's training set.
- Updating the knowledge base is a re-index, not a retraining run.
- You can show the user which document the answer came from.
- A small model plus good retrieval often beats a large model with no context.

## Limitation To Understand Early
RAG can only be as good as its retrieval step. If the right passage is never
retrieved, no amount of prompt engineering will produce a correct answer. When a RAG
system gives a bad answer, inspect the retrieved chunks first.

## Contrast: CAG
Cache-Augmented Generation skips retrieval entirely and puts every document into the
context window. It is simpler and has no chunking or vector store, but it does not
scale past what the context window holds.
