# -*- coding: utf-8 -*-
import os
import yaml

from pathlib import Path


class ConfigParser:
    """Extracts the data from the configuration file given"""
    def __new__(cls, path):
        with open(path, 'r') as f:
            contents = f.read()
            return yaml.safe_load(contents)


_path_to_config = Path(os.environ['PUBLISH_CONFIG'])
config = ConfigParser(_path_to_config)
