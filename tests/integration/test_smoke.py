import pytest

from src.service import DATABASE, DB, TABLE, SCHEMA, CONSUMER as consumer


"""These tests ensure that kafka consumer and DB connector are properly configured
and the overall setup (including Aiven services) is working"""


@pytest.mark.smoke
@pytest.mark.slow
def test_smoke_kafka_consumer():
    with consumer:
        consumer.fetch_latest()


@pytest.mark.smoke
def test_smoke_data_base():
    DATABASE(DB).execute_sql(f"SELECT * FROM {SCHEMA}.{TABLE} WHERE comment='test'")
