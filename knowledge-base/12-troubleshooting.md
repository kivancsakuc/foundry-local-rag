---
title: Troubleshooting Guide
category: Setup
id: DOC-SU-003
---

# Troubleshooting Guide

## Request To Local Service Failed
The local inference service is not running or has become unresponsive. Restart it:

    foundry server restart

This is the single most common error after a fresh install and is usually the fix.

## Model Download Appears To Hang
The first catalog listing or first model load contacts the catalog and can take
several minutes. Check available disk space before assuming failure. Model weights
range from a few hundred megabytes to several gigabytes. The cache listing command
shows what is already downloaded.

## Model Alias Not Found
The alias does not exist in the current catalog. List the catalog and use an alias
from the output. Aliases change between catalog releases.

## Windows ML Requires A Real GPU
The Windows SDK package requires a DirectX 12 capable GPU. Virtual machines without
GPU passthrough are not supported. On such a machine, use the cross-platform
foundry-local-sdk package instead of the winml variant.

## better-sqlite3 Fails To Build
npm is compiling the native module from source because no prebuilt binary matches the
installed Node version. Either install a C++ toolchain, or upgrade better-sqlite3 to
a major version that ships a binary for your Node release.

## Retrieval Returns Irrelevant Chunks
Inspect the retrieved chunks before blaming the model. Common causes: chunk size too
large so the signal is diluted, chunk size too small so context is lost, or a
tokeniser that strips the characters your documents are written in.

## Answers Ignore The Retrieved Context
The system prompt is not constraining the model. Confirm the context is actually being
inserted into the system message, and that the instruction to use only that context is
present.
