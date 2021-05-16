import logging
import pytest


@pytest.fixture(scope="package", autouse=True)
def logger():
    return logging.getLogger(__name__)
