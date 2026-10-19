# Phase 5 local runtime readiness (19 October 2026)

Observed on this development machine: macOS Darwin arm64, Apple M3 (10 GPU cores, Metal 4), 16 GiB unified memory. Ollama 0.35.1 is installed and its local HTTP service responds. No CUDA/NVIDIA GPU was observed. `python -m scripts.check_models` queried `/api/tags` without downloading weights.

| Selected checkpoint | Ollama tag | Quantization | Approximate download | Local status | Real inference |
|---|---|---|---:|---|---|
| `meta-llama/Llama-3.2-3B-Instruct` | `llama3.2:3b-instruct-q4_K_M` | Q4_K_M | 2.0 GB | Not installed | Not tested |
| `mistralai/Mistral-7B-Instruct-v0.3` | `mistral:7b-instruct-v0.3-q4_K_M` | Q4_K_M | 4.4 GB | Not installed | Not tested |

The local runtime currently has unrelated models installed; the application never selects them. Both configured Ollama tags are present in the official catalog, but no local digest or exact underlying Hugging Face commit can be recorded until they are downloaded. At first successful installation, `/api/tags` provides the artifact digest, which is stored with each generation. Model load behavior and multilingual output quality remain untested on this machine.

The M3's unified memory makes Q4 models plausible individually, but runtime memory needs also depend on context and concurrent processes. This report does not claim successful execution. See the [Ollama Llama tag](https://ollama.com/library/llama3.2/tags), [Ollama Mistral tag](https://ollama.com/library/mistral/tags), [Meta checkpoint](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct), and [Mistral checkpoint](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3).
