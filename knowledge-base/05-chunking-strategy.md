---
title: Document Chunking Strategy
category: Pipeline
id: DOC-PP-001
---

# Document Chunking Strategy

## Summary
Documents are split into smaller passages, called chunks, before indexing. Retrieval
returns chunks, not whole documents, so chunk size directly controls answer quality.

## Why Chunk At All
- A whole document usually will not fit in a small model's context window.
- A document covers several topics; only one paragraph may be relevant.
- Precision improves when the retrieved unit is the size of an actual answer.

## Chunk Size Trade-Off
- Too large: the chunk carries irrelevant text that dilutes the context and wastes
  the context window.
- Too small: the chunk loses the surrounding sentences needed to make sense of it,
  and the answer becomes fragmentary.

The configuration used in this program is roughly 200 tokens per chunk. Token counts
are approximated by whitespace-separated word counts, which is accurate enough for
retrieval work.

## Overlap
Consecutive chunks share a small overlap, around 25 tokens. Without overlap, a
sentence that straddles a chunk boundary is split and neither half retrieves well.
Overlap costs a little storage and removes an entire class of failure.

    def chunk_text(text, max_tokens=200, overlap_tokens=25):
        words = text.split()
        if len(words) <= max_tokens:
            return [text]
        chunks, start = [], 0
        while start < len(words):
            end = min(start + max_tokens, len(words))
            chunks.append(" ".join(words[start:end]))
            if end >= len(words):
                break
            start = end - overlap_tokens
        return chunks

## Respect Document Structure
Splitting on paragraph or heading boundaries produces better chunks than splitting on
a fixed word count alone, because the author already grouped related ideas together.

## Choosing topK
The topK setting controls how many chunks are passed to the model. Three is a good
default. Too few risks missing the answer; too many fills the context window with
noise and slows generation on a small model.
