#!/usr/bin/env python3
"""Convert Markdown cookbook recipes into CLI-compatible recipe JSON."""

import glob
import json
import os
import re
import sys
from pathlib import Path

import tomllib


def parse_recipe(path: Path) -> tuple[dict, int | None, Path | None, Path | None]:
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
    ingredients = []
    for line in sections.get('ingredients', []):
        item = re.sub(r'^[-*+]\s+', '', line)
        annotation = re.search(r'<!--\s*mc-ingredient:\s*(\{.*\})\s*-->', item)
        details = json.loads(annotation.group(1)) if annotation else {}
        if annotation:
            item = item[: annotation.start()].strip()
        if not isinstance(details, dict):
            raise ValueError('mc-ingredient annotation must be a JSON object')
        ingredients.append(
            {
                'name': item,
                'amount': details.get('amount', ''),
                'unit': details.get('unit', ''),
                'isOptional': details.get('isOptional', False),
            }
        )
    steps = []
    for line in sections.get('steps', []):
        item = re.sub(r'^\d+[.)]\s+', '', line)
        annotation = re.search(r'<!--\s*mc-mode:\s*(\{.*\})\s*-->', item)
        mode = json.loads(annotation.group(1)) if annotation else None
        if annotation:
            item = item[: annotation.start()].strip()
        title_match = re.match(r'^\*\*(.+?)\*\*:\s*(.*)$', item)
        step_title = title_match.group(1) if title_match else metadata.get('title', path.stem)
        description = title_match.group(2) if title_match else item
        if mode is not None and not isinstance(mode, dict):
            raise ValueError('mc-mode annotation must be a JSON object')
        steps.append({'title': step_title, 'description': description, 'mode': mode})
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

    def asset_path(field: str) -> Path | None:
        value = metadata.get(field)
        if value is None:
            return None
        if not isinstance(value, str) or not value:
            raise ValueError(f'{field} must be a non-empty path string')
        asset = Path(value).expanduser()
        if not asset.is_absolute():
            asset = path.parent / asset
        asset = asset.resolve()
        if not asset.is_file():
            raise ValueError(f'{field} image file does not exist: {asset}')
        return asset

    thumbnail_path = asset_path('thumbnail')
    details_image_path = asset_path('detailsImage')
    ingredient_groups = [
        {
            'name': metadata.get('ingredientGroupName', ''),
            'isDefault': True,
            'ingredients': ingredients,
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
                'steps': steps,
            }
        ],
    }
    for optional in ('categoryIds', 'complexityId', 'hintsAndTips', 'nutrients'):
        if optional in metadata:
            payload[optional] = metadata[optional]
    return payload, recipe_id, thumbnail_path, details_image_path


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
            payload, recipe_id, thumbnail_path, details_image_path = parse_recipe(path)
            target = output / f'{path.stem}.json'
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            id_path = target.with_suffix('.id')
            if recipe_id is not None:
                id_path.write_text(f'{recipe_id}\n', encoding='utf-8')
            else:
                id_path.unlink(missing_ok=True)
            for suffix, asset in (('.thumbnail', thumbnail_path), ('.details-image', details_image_path)):
                asset_sidecar = target.with_suffix(suffix)
                if asset is None:
                    asset_sidecar.unlink(missing_ok=True)
                else:
                    asset_sidecar.write_text(f'{asset}\n', encoding='utf-8')
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
