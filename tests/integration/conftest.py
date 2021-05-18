import logging
import pytest
from src.service import db


@pytest.fixture(scope="package")
def db_client():
    db.delete_data(comment='test')
    yield db
    db.delete_data(comment='test')
