---
title: Choosing A Local Chat Model
category: Platform
id: DOC-PL-002
---

# Choosing A Local Chat Model

## Summary
For a time-boxed teaching program, response latency matters more than answer
sophistication. Start with the smallest model that works and only grow if needed.

## Recommended Starting Point
The alias qwen2.5-0.5b, roughly half a billion parameters. It responds fast enough
that a student can iterate on a prompt, see the effect, and iterate again within a
single train of thought.

## Other Options In The Catalog
- phi-3.5-mini: around 2 GB. Better answers, noticeably slower on CPU.
- phi-4-mini: a newer small model in the same family.

## Why Not A 3 To 5 Billion Parameter Model
A 3B model on CPU can take ten seconds or more per answer. In a one-month program
where students are constantly changing a prompt and re-running, that latency destroys
the feedback loop. The learning value of a faster iteration cycle outweighs the
quality gain from a larger model.

Once the pipeline works end to end, swapping the model alias is a one-line change.
Let students make that upgrade themselves in the final week and observe the trade-off
directly. That comparison is a better lesson than starting large.

## Aliases Must Be Verified
Model aliases change between catalog releases. Always confirm with the catalog listing
command before committing an alias to teaching material. An alias that does not exist
produces a confusing failure at download time rather than a clear error.

## Note On A Common Mistake
There is no model alias called phi-1.5-mini. Earlier drafts of this curriculum
referenced it. Use a verified alias from the catalog instead.
