# Installation

Get ORC up and running in minutes.

---

## Standard Installation

Install ORC from PyPI:

```bash
pip install orc-arena
```

This installs the core framework with no LLM dependencies. You can use it with mock agents right away.

---

## With LLM Providers

ORC works with any LLM provider. Install with provider-specific dependencies:

### OpenAI (GPT-4, GPT-3.5, etc.)

```bash
pip install orc-arena[openai]
```

Requires an OpenAI API key. Set it via environment:

```bash
export OPENAI_API_KEY="sk-..."
```

### Anthropic (Claude)

```bash
pip install orc-arena[anthropic]
```

Requires an Anthropic API key:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Ollama (Local Models)

```bash
pip install orc-arena[ollama]
```

Requires Ollama running locally. No API key needed. Download models from [ollama.ai](https://ollama.ai).

```bash
ollama pull qwen2.5:72b  # or any available model
```

### All Providers

```bash
pip install orc-arena[all]
```

Installs support for OpenAI, Anthropic, and Ollama. Pick which ones you use.

---

## Development Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/Lumi-node/ORC.git
cd ORC

pip install -e ".[dev]"  # Installs dev dependencies, tests, examples
```

Run tests to verify:

```bash
pytest tests/ -v
```

Run the quick battle example (no LLM needed):

```bash
python examples/quick_battle.py
```

---

## Verify Installation

Test that ORC is installed and ready:

```bash
python -c "from orc import Arena, Warrior, Elder; print('Ready for battle')"
```

You should see:

```
Ready for battle
```

---

## Docker

ORC includes a Dockerfile. Build and run:

```bash
docker build -t orc .
docker run orc
```

---

## Python Compatibility

ORC requires **Python 3.10+**. Check your version:

```bash
python --version
```

---

## Next Steps

- **[Quick Start](quick-start.md)** — Run your first battle
- **[Core Concepts](concepts.md)** — Understand Warriors, Elders, and The Arena
- **[Model Showdown](../guides/model-showdown.md)** — Compare LLMs head-to-head
