---
title: Prompt Engineering For Grounded Question Answering
category: Concepts
id: DOC-CN-002
---

# Prompt Engineering For Grounded Question Answering

## Summary
Retrieving the right passage is only half the job. How that passage is presented to
the model determines whether the answer is grounded, concise, and honest.

## System Message Versus User Message
Chat models take a list of messages with roles. The system message sets standing
instructions and carries the retrieved context. The user message carries the question.
Keeping them separate makes the model treat the context as reference material rather
than as something to respond to.

    messages = [
        {"role": "system", "content": system_instructions_plus_context},
        {"role": "user", "content": query},
    ]

## Instructions That Earn Their Place
- Restrict to context. Tell the model to answer using only the provided context.
  Without this the model falls back on training data and the grounding is lost.
- Permit ignorance. Tell it to say so when the context is insufficient. A model that
  cannot admit ignorance will invent an answer instead.
- Cite the source. If each chunk carries its source filename, ask the model to name
  it. This lets the user verify the answer.
- Constrain length. Small models ramble. An explicit brevity instruction helps.

## Testing The Refusal Path
Every RAG system must be tested with a question whose answer is deliberately absent
from the knowledge base. If the assistant answers it confidently, the system prompt is
not working, regardless of how well it handles questions it can answer. This test is
not optional.

## Format Instructions
Asking for a fixed shape, such as a one-line summary followed by steps and then a
reference, produces noticeably more usable output from a small model than leaving the
format open.
