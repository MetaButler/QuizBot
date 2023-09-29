import yaml
from typing import Any

def load_config(filename: str) -> Any:
    with open(filename, "r") as yaml_file:
        config = yaml.safe_load(yaml_file)
    return config