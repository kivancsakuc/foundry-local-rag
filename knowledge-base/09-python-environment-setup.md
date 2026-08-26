---
title: Python Environment Setup
category: Setup
id: DOC-SU-001
---

# Python Environment Setup

## Recommended Python Version
Python 3.12. The Foundry Local SDK declares support for 3.11 and later, but its
published classifiers cover 3.11, 3.12, and 3.13. Newer releases such as 3.14 are
untested territory. In a program with many students, a tested version is worth the
five minutes it takes to install.

    winget install Python.Python.3.12

Installing 3.12 alongside an existing Python does not disturb the existing one. On
Windows the launcher selects between them:

    py -3.12 --version

## Virtual Environment
Always work in a virtual environment so project dependencies stay isolated:

    py -3.12 -m venv .venv
    .venv\Scripts\activate

On macOS and Linux the activation command is:

    source .venv/bin/activate

## Installing The SDK
The package name differs by platform. On Windows:

    pip install foundry-local-sdk-winml openai

On macOS and Linux:

    pip install foundry-local-sdk openai

The openai package is required in both cases because the SDK chat and embedding
clients build on it.

## Common Mistake
Installing plain foundry-local-sdk on Windows. It will install, but the Windows build
integrates with the Windows ML runtime and gives access to a wider range of hardware
acceleration. Use the winml variant on Windows.
