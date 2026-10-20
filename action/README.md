# Monsieur Cuisine cookbook action

This composite GitHub Action validates Markdown recipes and converts each one to a JSON payload accepted by `monsieur-cuisine-cli recipes create --data`.

## Recipe format

Store recipes as `.md` files under `recipes/`. Put recipe metadata in a visible Markdown table under `## Recipe`, then add `## Ingredients` and `## Steps` sections.

```markdown
## Recipe

| Field | Value |
| --- | --- |
| title | Tomato soup |
| languageLocale | en-US |
| deviceTypeIds | 13 |
| servings | 4 |
| preparationTime | 10 |
| readyInTime | 35 |
| description | A simple weeknight soup. |

## Ingredients

- 800 g ripe tomatoes
- 1 onion, quartered
- 500 ml vegetable stock

## Steps

1. Chop the onion for 5 seconds at speed 5.
2. Add tomatoes and stock. Cook for 25 minutes at 100°C, speed 2.
3. Blend for 1 minute, increasing gradually to speed 8.
```

Required table fields: `title`, `languageLocale`, `deviceTypeIds` (one or more integer IDs; comma-separated values are accepted), and `servings` (positive integer). Optional fields: `recipeId` (positive integer; selects update instead of create when publishing), `thumbnail` and `detailsImage` (image paths relative to the Markdown file), `ingredientGroupName`, `status` (defaults to `draft`), `description`, `servingUnit` (defaults to `servings`), `preparationTime`, `readyInTime`, `categoryIds`, `complexityId`, `hintsAndTips`, and `nutrients`.

Nutrition can be supplied as a table under `## Nutrition` with `Nutrient`, `Amount`, and `Unit` columns. Ingredient lines are converted to ingredient entries with their text in `name`; steps become manual recipe steps with `mode: null`. The action does not infer machine modes, quantities, or units from prose. Review the generated JSON before publishing, and use `recipes get` to inspect existing recipes for the exact device-specific mode schema your cooker uses.

To retain structured ingredient data or machine modes, append hidden Markdown annotations to the readable line: `<!-- mc-ingredient: {"amount":"100","unit":"g","isOptional":false} -->` and `<!-- mc-mode: {"type":"slow_cooking","deviceSettings":[{"time":900,"temperature":50,"order":0}]} -->`. When publishing, declared images are passed to the CLI's image-upload options for both creation and update; the generated payload never reuses old API media IDs.

## Use in a cookbook repository

```yaml
name: Validate cookbook
on:
  pull_request:
  push:
    branches: [main]
jobs:
  recipes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: fopina/monsieur-cuisine-cli@github-action-cookbook
        id: cookbook
      - uses: actions/upload-artifact@v4
        with:
          name: recipe-json
          path: ${{ steps.cookbook.outputs.output-directory }}
```

Inputs `recipes` and `output` can override the defaults `recipes/**/*.md` and `build/recipes`. A missing recipe match or invalid recipe fails the action. Generated files are named after their Markdown file and written as UTF-8 JSON.
