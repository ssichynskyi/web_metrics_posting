import datetime
import pytest

from src.service import SCHEMA, TABLE
from tests.mocks.consumer import consumer


@pytest.mark.integration
def test_db_wrapper_integration(db_client):
    data = consumer.fetch_latest()
    inserted_rows = db_client.insert(data, schema=SCHEMA, table=TABLE)
    for row in inserted_rows:
        assert row in EXPECTED, f'Row from DB doesnt match with expected: {row}'
    for row in EXPECTED:
        assert row in inserted_rows, f'Expected row is missing in DB: {row}'


EXPECTED = [
    (
        datetime.datetime(2021, 1, 1, 0, 0),
        'https://www.monedo.com/',
        'Web metric collection service',
        datetime.timedelta(microseconds=123000),
        200,
        '104.18.91.87',
        True,
        'test'
    ),
    (
        datetime.datetime(2021, 1, 1, 0, 0),
        'https://www.monedo.com/',
        'Web metric collection service',
        datetime.timedelta(microseconds=123000),
        200,
        '104.18.91.87',
        True,
        'test'
    ),
    (
        datetime.datetime(2021, 1, 1, 0, 0),
        'https://www.monedo.com/',
        'Web metric collection service',
        None,
        200,
        None,
        None,
        'test'
    )
]
