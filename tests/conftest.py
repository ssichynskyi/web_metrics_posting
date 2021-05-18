import logging
import pytest


@pytest.fixture(scope="package", autouse=True)
def example():
    log = logging.getLogger('example')
