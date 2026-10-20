#!/usr/bin/env python3
"""Convert Markdown cookbook recipes into CLI-compatible recipe JSON."""

import glob
import json
import os
import re
import sys
from pathlib import Path

import tomllib


def parse_recipe(path: Path) -> tuple[dict, int | None]:
    text = path.read_text(encoding='utf-8')
    if not text.startswith('+++\n'):
        raise ValueError('expected TOML front matter delimited by +++')
    try:
        _, metadata_text, body = text.split('+++', 2)
        metadata = tomllib.loads(metadata_text)
    except (ValueError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f'invalid TOML front matter: {exc}') from exc
    sections = {}
    current = None
    for line in body.splitlines():
        heading = re.match(r'^##\s+(.+?)\s*$', line)
        if heading:
            current = heading.group(1).strip().lower()
            sections[current] = []
        elif current and line.strip():
            sections[current].append(line.strip())
    ingredients = [re.sub(r'^[-*+]\s+', '', line) for line in sections.get('ingredients', [])]
    steps = [re.sub(r'^\d+[.)]\s+', '', line) for line in sections.get('steps', [])]
    required = ('title', 'languageLocale', 'deviceTypeIds', 'servings')
    missing = [field for field in required if field not in metadata]
    if missing:
        raise ValueError(f'missing front matter fields: {", ".join(missing)}')
    if not ingredients:
        raise ValueError('add at least one item under ## Ingredients')
    if not steps:
        raise ValueError('add at least one numbered item under ## Steps')
    servings = metadata['servings']
    if not isinstance(servings, int) or isinstance(servings, bool) or servings < 1:
        raise ValueError('servings must be a positive integer')
    device_ids = metadata['deviceTypeIds']
    if not isinstance(device_ids, list) or not device_ids or any(type(value) is not int for value in device_ids):
        raise ValueError('deviceTypeIds must be a non-empty list of integer IDs')
    recipe_id = metadata.get('recipeId')
    if recipe_id is not None and (not isinstance(recipe_id, int) or isinstance(recipe_id, bool) or recipe_id < 1):
        raise ValueError('recipeId must be a positive integer')
    ingredient_groups = [
        {
            'name': '',
            'isDefault': True,
            'ingredients': [{'name': value, 'amount': '', 'unit': '', 'isOptional': False} for value in ingredients],
        }
    ]
    payload = {
        'status': metadata.get('status', 'draft'),
        'source': 'member',
        'languageLocale': metadata['languageLocale'],
        'deviceTypeIds': device_ids,
        'title': metadata['title'],
        'description': metadata.get('description', ''),
        'servingSizes': [
            {
                'amount': servings,
                'isDefault': True,
                'unit': metadata.get('servingUnit', 'servings'),
                'instruction': '',
                'preparationTime': int(metadata.get('preparationTime', 0)),
                'readyInTime': int(metadata.get('readyInTime', 0)),
                'ingredientGroups': ingredient_groups,
                'steps': [{'title': metadata['title'], 'description': value, 'mode': None} for value in steps],
            }
        ],
    }
    for optional in ('categoryIds', 'complexityId', 'hintsAndTips'):
        if optional in metadata:
            payload[optional] = metadata[optional]
    return payload, recipe_id


def main() -> int:
    recipe_glob = os.environ.get('RECIPE_GLOB', 'recipes/**/*.md')
    files = sorted(Path(name) for name in glob.glob(recipe_glob, recursive=True) if Path(name).is_file())
    if not files:
        print(f'No recipe files matched {recipe_glob!r}', file=sys.stderr)
        return 1
    output = Path(os.environ.get('OUTPUT_DIR', 'build/recipes'))
    output.mkdir(parents=True, exist_ok=True)
    failed = False
    for path in files:
        try:
            payload, recipe_id = parse_recipe(path)
            target = output / f'{path.stem}.json'
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            id_path = target.with_suffix('.id')
            if recipe_id is not None:
                id_path.write_text(f'{recipe_id}\n', encoding='utf-8')
            else:
                id_path.unlink(missing_ok=True)
            print(f'Converted {path} -> {target}')
        except (OSError, ValueError, TypeError) as exc:
            failed = True
            print(f'{path}: {exc}', file=sys.stderr)
    output_file = os.environ.get('GITHUB_OUTPUT')
    if output_file:
        with open(output_file, 'a', encoding='utf-8') as handle:
            handle.write(f'output-directory={output.as_posix()}\n')
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
