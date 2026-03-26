# Contributing to ORC Documentation

This guide is for maintaining and updating the ORC documentation site.

---

## Local Setup

### First Time

```bash
cd /mnt/4TB_SSD_1/ORC
python -m venv .venv
source .venv/bin/activate
pip install mkdocs-material "mkdocstrings[python]"
```

### Build and Serve

```bash
source .venv/bin/activate
mkdocs serve
```

Then open http://localhost:8000

---

## File Structure

```
docs/
├── index.md                          # Landing page
├── built-with.md                     # Built with dynabots-core
├── getting-started/
│   ├── installation.md               # How to install ORC
│   ├── quick-start.md                # Quick start example
│   └── concepts.md                   # Core concepts explained
├── guides/
│   ├── model-showdown.md             # Compare models
│   ├── custom-judges.md              # Build custom judges
│   ├── strategies.md                 # Challenge strategies
│   └── use-cases.md                  # Real-world use cases
└── reference/
    ├── arena.md                      # Arena API (auto-generated)
    ├── warrior.md                    # Warrior API (auto-generated)
    ├── elder.md                      # Elder API (auto-generated)
    ├── judges.md                     # Judges API (auto-generated)
    └── strategies.md                 # Strategies API (auto-generated)
```

---

## Editing Guide

### Creating a New Page

1. Create `.md` file in the appropriate directory
2. Add to navigation in `mkdocs.yml`
3. Run `mkdocs serve` to preview
4. Check links and formatting

### Writing Content

- Use Markdown syntax
- Code fences with language: ` ```python ... ``` `
- Headings: `#` (H1), `##` (H2), `###` (H3)
- Links: `[text](url)`
- Images: `![alt](path)`

### Code Examples

Always provide working examples:

```python
# Good: Complete, runnable example
import asyncio
from orc import TheArena, Warrior, Elder

async def main():
    warrior = Warrior(...)
    elder = Elder(...)
    arena = TheArena(...)
    result = await arena.battle("task")
    print(result.winner)

asyncio.run(main())
```

```python
# Avoid: Incomplete snippets
arena = TheArena(...)  # Missing imports and setup
```

### API Reference Pages

Reference pages use auto-generation via `mkdocstrings`:

```markdown
# Arena

The core orchestration component.

::: orc.arena.arena.Arena
    options:
      docstring_style: google
```

This pulls docstrings directly from Python source code. Keep docstrings updated in the code:

```python
class Arena:
    """Brief description.

    Longer description with example.

    Example:
        arena = Arena(agents=[...], judge=...)
        result = await arena.process("task")

    Args:
        agents: List of agents.
        judge: Judge to evaluate trials.
    """
```

---

## Theme Configuration

Edit `mkdocs.yml` to customize:

### Colors

```yaml
theme:
  palette:
    - scheme: slate      # Dark theme
      primary: red       # Change to blue, green, etc.
      accent: deep orange
    - scheme: default    # Light theme
      primary: red
      accent: deep orange
```

### Fonts

```yaml
  font:
    text: Inter
    code: JetBrains Mono
```

### Navigation

```yaml
nav:
  - Home: index.md
  - Section Name:
    - Page Title: path/to/page.md
```

### Plugins

Currently enabled:
- `search` — Full-text search
- `mkdocstrings` — Auto-generate API docs from docstrings

---

## Deployment

### Manual Deploy

```bash
source .venv/bin/activate
mkdocs gh-deploy --force
```

This builds and deploys to `gh-pages` branch.

### Automatic Deploy

Push to `main` branch. GitHub Actions automatically:
1. Installs dependencies
2. Builds documentation
3. Deploys to GitHub Pages

Workflow file: `.github/workflows/docs.yml`

---

## Content Guidelines

### Tone

- **Friendly but professional** — Use ORC theming (Warriors, Warchiefs) but stay clear
- **Practical** — Include working code examples
- **Thorough** — Explain the "why" not just the "how"

### Structure

- **Lead with use case** — Why would someone use this?
- **Show code first** — Working example early
- **Explain concepts** — Deep dive into mechanics
- **Provide patterns** — How to apply in real scenarios

### Code Style

- Match project's Python style
- Use type hints
- Include docstrings
- Comment complex logic

---

## Common Tasks

### Update Installation Guide

Edit `docs/getting-started/installation.md`
- Add new provider support
- Update version requirements
- Add new installation options

### Add a New Guide

1. Create `docs/guides/your-guide.md`
2. Add to `mkdocs.yml` under Guides
3. Link from other pages if relevant
4. Test locally: `mkdocs serve`

### Update API Reference

API reference pages are auto-generated from Python docstrings. To update:
1. Edit docstring in source code (e.g., `orc/arena/arena.py`)
2. The docs will auto-regenerate on next build
3. Run `mkdocs serve` to see changes

---

## Troubleshooting

### Build fails

```bash
source .venv/bin/activate
pip install --upgrade mkdocs-material mkdocstrings[python]
mkdocs build
```

### Links are broken

Check the path. Link paths should be relative:
- Good: `../../reference/arena.md` or `../guides/custom-judges.md`
- Bad: `/docs/reference/arena.md`

### Code not highlighting

Ensure fence language is specified:
- Good: ` ```python ... ``` `
- Bad: ` ```code ... ``` ` or ` ```python ... ``` ` (without language)

### Missing content in API reference

Check that:
1. Module/class path is correct in `.md` file
2. Docstrings exist in Python source
3. Docstring style matches config (Google style)

---

## Preview Before Publishing

Always run locally:

```bash
mkdocs serve
```

Test:
- Links (click around)
- Code examples (are they readable?)
- Dark/light mode toggle
- Mobile responsiveness (resize browser)
- Search functionality

---

## Publishing Checklist

Before pushing to main:

- [ ] Ran `mkdocs serve` and verified
- [ ] All links work
- [ ] Code examples are complete and correct
- [ ] No spelling/grammar errors
- [ ] Consistent with existing style
- [ ] Added to navigation if new page
- [ ] Tested dark and light themes

---

## Questions?

Refer to:
- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [mkdocstrings](https://mkdocstrings.github.io/)

---

Happy documenting!
