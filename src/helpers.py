import json
import yaml
from pathlib import Path
from typing import Any


# Config Loading
def load_config_file(path: Path) -> Any:
    if path.suffix == '.yaml':
        return _load_from_yaml(path)
    if path.suffix == '.json':
        return _load_from_json(path)
    else:
        raise NotImplementedError(f"{path.suffix} filetype not yet supported")

def _load_from_json(path) -> Any:
    with open(path) as file:
        return json.load(file)

def _load_from_yaml(path) -> Any:
    with open(path) as file:
        return yaml.safe_load(file)
