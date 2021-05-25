import pytest


@pytest.fixture(scope="package", autouse=True)
def example():
    pass
