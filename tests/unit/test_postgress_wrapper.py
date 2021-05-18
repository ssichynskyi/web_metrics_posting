import pytest

from src.postgres_wrapper import WebMonitoringDBWrapper
from tests.mocks.db_lib_mock import mock_db_lib, mock_db_active_cursor
from tests.mocks.consumer import consumer


@pytest.mark.unit
def test_insert_query_creation():
    db = WebMonitoringDBWrapper('mock-db', 'user', 'password', 'host', 'port')
    db.insert(consumer.fetch_latest(), db_lib=mock_db_lib)
    mock_db_lib.connect.assert_called_once_with(**db._connection_params)
    for part in EXPECTED_ARGS_INSERT:
        assert part in mock_db_active_cursor.execute.call_args_list[0][0][0]


@pytest.mark.unit
def test_delete_query_not_possible_with_no_params():
    mock_db_active_cursor.execute.reset_mock()
    db = WebMonitoringDBWrapper('mock-db', 'user', 'password', 'host', 'port')
    db.delete_data(db_lib=mock_db_lib)
    mock_db_active_cursor.execute.assert_not_called()


@pytest.mark.unit
def test_delete_query_creation():
    mock_db_active_cursor.execute.reset_mock()
    db = WebMonitoringDBWrapper('mock-db', 'user', 'password', 'host', 'port')
    db.delete_data(db_lib=mock_db_lib, comment='test')
    for part in EXPECTED_ARGS_DELETE:
        assert part in mock_db_active_cursor.execute.call_args_list[0][0][0]


EXPECTED_ARGS_INSERT = [
    "INSERT INTO web_metrics.metrics(time_stamp, url, ip, response_time,"
    " status_code, content_validation, agent, comment)",
    "VALUES",
    "('2021-01-01 00:00:00', 'https://www.monedo.com/', '104.18.91.87', '0:00:00.123456',"
    " '200', 'True', 'Web metric collection service', 'test'), "
    "('2021-01-01 00:00:00', 'https://www.monedo.com/', '104.18.91.87', '0:00:00.123456',"
    " '200', 'True', 'Web metric collection service', 'test'), "
    "('2021-01-01 00:00:00', 'https://www.monedo.com/', NULL, NULL, '200', NULL, NULL, 'test')",
    "RETURNING *;"
]

EXPECTED_ARGS_DELETE = [
    "DELETE",
    "FROM web_metrics.metrics",
    "WHERE comment='test'",
    "RETURNING *;"
]
