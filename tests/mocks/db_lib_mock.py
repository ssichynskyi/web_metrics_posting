from unittest.mock import MagicMock


mock_db_lib = MagicMock()
mock_db_connection = MagicMock()
mock_db_cursor = MagicMock()
mock_db_active_cursor = MagicMock()

mock_db_lib.connect.return_value = mock_db_connection
mock_db_connection.cursor.return_value = mock_db_cursor
mock_db_cursor.__enter__.return_value = mock_db_active_cursor
mock_db_active_cursor.execute.return_value = None
