# Phase 6 deployment readiness

**Local demonstrator:** supported on the tested Apple M3, 16 GiB machine. Python 3.12.6, Node 24.11.1, npm 11.6.2, Next.js 16.3.4 and Ollama 0.35.1 were observed. The backend virtual environment, NLP artifacts and hybrid index are present. Ollama reported Llama at 2.5 GB and Mistral at 4.9 GB loaded, both 100% GPU with 4096 context during testing; these are model footprints, not measured total peak memory. The checkpoints were run sequentially and then released. The full tested startup and evaluation commands are in the root and backend READMEs.

**Online deployment:** not ready and not claimed. Persistent matter APIs have no user authentication or retention policy. A hosted architecture needs an authenticated frontend/API, private database and access-controlled model-serving host with sufficient RAM/storage; ordinary serverless hosting will not run both local checkpoints. Do not expose this backend or SQLite database to the public internet. No public URL exists.

**Dataset/legal gate:** original validator still reports two critical errors. The research overlay leaves one. Only four legal provisions are eligible; independent legal review is outstanding. Model weights and SQLite contents remain outside Git.
