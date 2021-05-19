import logging
import pytest
from src.service import DATABASE


@pytest.fixture(scope="package")
def db_client():
    DATABASE.delete_data(comment='test')
    yield DATABASE
    DATABASE.delete_data(comment='test')
