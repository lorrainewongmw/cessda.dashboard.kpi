# SP's KPIs

SP's main KPIs over 2020–2024.

## Prerequisites

- [Nix](https://nixos.org/download) with flakes enabled
- [devenv](https://devenv.sh/getting-started/)

## Setup

```bash
devenv shell

uv run python -m ipykernel install --user --name=sp-analysis --display-name="sp-analysis"

uv run jupyter notebook
```

Then open `analysis.ipynb` and select the **sp-analysis** kernel via **Kernel → Change Kernel**.

## Dependencies

Managed by `uv` — see `pyproject.toml`. Key packages: `pandas`, `altair`, `jupyter`, `ipykernel`.

To add a new dependency:

```bash
uv add package-name
```
