import pytest
from src.service import DATABASE, DB, SCHEMA, TABLE


@pytest.fixture(scope="package")
def db_client():
    db = DATABASE(DB)
    db.delete_data(schema=SCHEMA, table=TABLE, comment='test')
    yield db
    db.delete_data(schema=SCHEMA, table=TABLE, comment='test')
