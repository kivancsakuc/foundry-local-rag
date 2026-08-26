---
title: What Is Foundry Local
category: Platform
id: DOC-PL-001
---

# What Is Foundry Local

## Summary
Foundry Local is Microsoft's on-device AI runtime. It downloads, manages, and runs
large language models entirely on the user's own machine. No cloud account, no API
key, and no network call at inference time.

## Why It Matters For This Program
The whole point of this summer school project is that the finished assistant runs
offline. Foundry Local is what makes that possible. Students can unplug the network
cable and the assistant keeps answering.

## Key Capabilities
- Model catalog: a curated set of models optimised for local execution, in ONNX format.
- Automatic download and caching: the first run pulls the weights, later runs reuse them.
- Hardware acceleration: it selects CPU, GPU, or NPU automatically.
- SDKs: Python, C#, JavaScript, and Rust bind to the same local runtime.
- OpenAI-compatible surface: the chat client mirrors the familiar chat completions shape.

## Installation
On Windows, install the runtime with the Windows package manager:

    winget install Microsoft.FoundryLocal

Verify it with:

    foundry --version

The runtime version and the SDK version are numbered separately. The runtime is
versioned around 0.x while the Python SDK is versioned around 1.x. This is expected
and is not a sign of a mismatch on its own.

## Useful CLI Commands
- foundry model list: show the catalog of available models.
- foundry model run ALIAS: load a model and open an interactive prompt.
- foundry cache list: show which model weights are already on disk.
- foundry server restart: restart the local inference service.

## Hardware Requirement On Windows
The Windows SDK package integrates with the Windows ML runtime, which requires a real
DirectX 12 capable GPU. Virtual machines without GPU passthrough are not supported.
If the teaching lab runs on VMs, confirm GPU passthrough before the program starts,
or plan to use the cross-platform package instead.
