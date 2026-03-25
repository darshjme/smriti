<div align="center">

<img src="assets/smriti-hero.png" alt="स्मृति — smriti by Darshankumar Joshi" width="100%" />

# 🪷 स्मृति
## `smriti`

> *Vedic Smriti tradition*

### Sacred Memory — the 18 Smritis

**Multi-backend caching for LLM agents: memory, disk, Redis-compatible interface. TTL, LRU, semantic cache.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)](https://python.org)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero-brightgreen?style=flat-square)](https://github.com/darshjme/smriti)
[![Vedic Arsenal](https://img.shields.io/badge/Vedic%20Arsenal-100%20libs-pink?style=flat-square)](https://github.com/darshjme/arsenal)
[![License](https://img.shields.io/badge/License-MIT-pink?style=flat-square)](LICENSE)

*Formerly `agent-cache` — Part of the [**Vedic Arsenal**](https://github.com/darshjme/arsenal): 100 production-grade Python libraries for LLM agents, each named from the Vedas, Puranas, and Mahakavyas.*

</div>

---

## The Vedic Principle

The eighteen *Smritis* — sacred texts of remembered law and tradition — preserved the Vedic wisdom across millennia without digital storage. Pure memory, encoded in verse, passed from guru to shishya.

`smriti` brings this sacred memory architecture to LLM agents. Semantic cache, exact cache, TTL-aware LRU — the agent remembers what it has learned. The TF-IDF similarity matching finds the memory that *feels* like the current question, even if the words differ.

*Smriti* means "that which is remembered." Every cached response is a memory. Every cache hit is the agent drawing on its accumulated wisdom rather than asking the universe the same question twice.

---

## How It Works

```mermaid
flowchart LR
    A[Input] --> B[smriti]
    B --> C{Process}
    C -- Success --> D[Output]
    C -- Error --> E[Handle]
    E --> B
    style B fill:#6b21a8,color:#fff
```

---

## Installation

```bash
pip install smriti
```

Or from source:
```bash
git clone https://github.com/darshjme/smriti.git
cd smriti && pip install -e .
```

## Quick Start

```python
from smriti import *

# See examples/ for full usage
```

---

## The Vedic Arsenal

`smriti` is one of 100 libraries in **[darshjme/arsenal](https://github.com/darshjme/arsenal)** — each named from sacred Indian literature:

| Sanskrit Name | Source | Technical Function |
|---|---|---|
| `smriti` | Vedic Smriti tradition | Sacred Memory — the 18 Smritis |

Each library solves one problem. Zero external dependencies. Pure Python 3.8+.

---

## Contributing

1. Fork the repo
2. Create feature branch (`git checkout -b fix/your-fix`)  
3. Add tests — zero dependencies only
4. Open a PR

---

<div align="center">

**🪷 Built by [Darshankumar Joshi](https://github.com/darshjme)** · [@thedarshanjoshi](https://twitter.com/thedarshanjoshi)

*"कर्मण्येवाधिकारस्ते मा फलेषु कदाचन"*
*Your right is to action alone, never to its fruits. — Bhagavad Gita 2.47*

[Vedic Arsenal](https://github.com/darshjme/arsenal) · [GitHub](https://github.com/darshjme) · [Twitter](https://twitter.com/thedarshanjoshi)

</div>
