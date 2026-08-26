---
title: Node.js Path Setup
category: Setup
id: DOC-SU-002
---

# Node.js Path Setup

## Requirements
Node.js 20 or later. The TF-IDF reference application declares this in the engines
field of its package.json.

## Dependencies
The application deliberately keeps its dependency list to three packages:

- express: the HTTP server.
- foundry-local-sdk: the JavaScript binding to the local runtime.
- better-sqlite3: synchronous SQLite access.

There is no embedding library and no vector database, because retrieval is TF-IDF.

## Running It

    npm install
    npm run ingest
    npm start

The ingest script reads every markdown file in the docs directory, produces
overlapping chunks, computes TF-IDF vectors, and writes everything to data/rag.db.
The start script loads the chat model through the SDK, opens the vector store, and
starts the Express server on port 3000.

## Native Module Compilation
better-sqlite3 is a native module. It ships prebuilt binaries for a set of Node
versions; if the installed Node is newer than that set, npm compiles from source and
a C++ toolchain is required. On Windows that means Visual Studio build tools with the
C++ workload. If compilation fails, upgrading better-sqlite3 to a newer major version
usually restores a matching prebuilt binary.

## Configuration
Tunable values live in src/config.js: the model alias, chunkSize, chunkOverlap, topK,
and the server port. The system prompt lives separately in src/prompts.js.
