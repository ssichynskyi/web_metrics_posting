# -*- coding: utf-8 -*-
import os
import yaml

from pathlib import Path

from utils.dict_merger import merge_dicts


class ConfigParser:
    """Extracts the data from the configuration file given."""
    def __new__(cls, path):
        if not Path.exists(path):
            return None
        with open(path, 'r') as f:
            contents = f.read()
            return yaml.safe_load(contents)


_project_root = Path(os.getenv('PROJECT_ROOT', Path(__file__).parent.parent))
_path_to_config_folder = _project_root.joinpath('config/')
_path_to_config = Path(
    os.getenv(
        'PUBLISH_CONFIG',
        _path_to_config_folder.joinpath('service.yaml')
    )
)
_path_to_local_config = Path(
    os.getenv(
        'PUBLISH_CONFIG_LOCAL',
        _path_to_config_folder.joinpath('service_local.yaml')
    )
)
config = ConfigParser(_path_to_config)
_config_local = ConfigParser(_path_to_local_config)
config = merge_dicts(config, _config_local)
