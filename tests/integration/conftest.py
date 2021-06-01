import pytest
from src.service import DATABASE, SCHEMA


@pytest.fixture(scope="package")
def db_client():
    db = DATABASE(SCHEMA)
    db.delete_data(comment='test')
    yield db
    db.delete_data(comment='test')
