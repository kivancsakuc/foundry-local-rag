---
title: Evaluating RAG Quality
category: Concepts
id: DOC-CN-003
---

# Evaluating RAG Quality

## Separate The Two Failure Modes
A wrong answer comes from either bad retrieval or bad generation. These have different
fixes, so diagnose which one before changing anything.

Always log or display the retrieved chunks. If the correct passage was never
retrieved, the generation step was never given a chance and prompt changes are wasted
effort.

## Retrieval Checks
- Was the passage containing the answer among the top-k results?
- If it was retrieved but ranked low, would a larger topK have helped?
- Are chunks split so that the answer straddles a boundary?

## Generation Checks
- Did the model use the supplied context, or fall back on its own knowledge?
- Did it admit ignorance when the context genuinely lacked the answer?
- Is the answer the right length and format?

## A Minimum Test Set
Write down at least ten questions before tuning anything:
- Six that the documents clearly answer.
- Two that require combining two different documents.
- Two that the documents definitely do not answer.

The last two are the most informative. A system that answers them anyway is
hallucinating, and that is a correctness bug, not a style problem.

## Latency
Measure and record response time for each architecture. On a laptop, a sub-billion
parameter model should answer in a small number of seconds. If it does not, reduce
topK, shorten chunks, or check that the model is not being reloaded on every request.

## Reporting
Record the question, the retrieved sources, the answer, and whether it was correct.
This table is the evidence base for the final report and makes tuning decisions
defensible rather than anecdotal.
