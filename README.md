# monsieur-cuisine-cli

A command-line client for managing recipes in a monsieur-cuisine.com account.

The goal is to make common account tasks available from the terminal, including
adding recipes, updating recipe details, and removing recipes. This project is
at an early stage: the current Python package is still the template demo, and
the account and recipe commands described here are planned rather than
implemented.

## Planned capabilities

- Connect to a monsieur-cuisine.com account.
- Add a recipe to the account.
- Update an existing recipe.
- Remove a recipe from the account.

Command names, authentication setup, and recipe input format will be
documented here as those features are implemented.

## Development

This project uses [uv](https://docs.astral.sh/uv/) for Python environment and
dependency management. Once the template is adapted, install the development
dependencies with:

```sh
uv sync --dev
```

The Python package template currently provides pytest and Ruff checks. See the
project's `Makefile` for the available development commands.

## Disclaimer

This is an unofficial community project and is not affiliated with or endorsed
by monsieur-cuisine.com or its operators. Use it only with an account you are
authorized to access, and follow the service's terms and applicable policies.
