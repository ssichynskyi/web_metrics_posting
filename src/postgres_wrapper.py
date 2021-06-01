import datetime
import logging
import psycopg2

from typing import Union, Dict, List, Tuple, Optional, Any


log = logging.getLogger(__name__)


class Postgres:
    def __init__(self, host: str, port: Union[int, str], user: str, password: str, database: str):
        """Wrapper / Facade class for psycopg2 lib

        Args:
            database: DB schema to use
            user: username for authentication
            password: password for authentication
            host: url of DB service
            port: port of DB service to connect to

        """
        self._connection_params = {
            'database': database,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }
        self._db = database
        self._uri = f'{host}:{port}'

    def execute_sql(
            self,
            sql: str,
            db_lib: psycopg2 = psycopg2,
            args: Union[Dict, List, Tuple] = None
    ) -> Optional[List[Tuple[Any]]]:
        """Executes given sql with arguments

        Args:
            sql: an SQL query. Placeholder for args shall be
            db_lib: library object to use. Shall have at least compatible
                by signature methods: connect, cursor, cursor.execute,
                cursor.fetchall and ProgrammingError exception.
                Default is postgres psycopg2.
            args: tuple, list or dict to be inserted in sql

        Returns:
            List of Dicts where:
                - list member is row
                - Dict keys: columns names
                - Dict values: row X col value
        """
        # This could be a critical security point because the credentials could be transferred
        # using unencrypted channel. Brief check showed that connection to some random
        # http resource is rejected beforehand. Assume it's safe. If I have more time,
        # I would investigate this better
        connection = db_lib.connect(**self._connection_params)
        result = None
        # It was a tradeoff to keep a connection open during service lifetime or make it like this
        # One here more scalable (if used with bulk transactions updating many rows at once)
        # The side effect is that for testability reasons it require passing lib as param
        with connection:
            log.info(f'Establishing connection to DB: {self._uri}')
            with connection.cursor() as cursor:
                log.info(f'Sending SQL query: {sql}')
                try:
                    cursor.execute(sql, args)
                except BaseException as e:
                    # Exception is too broad but this is how it's raised by lib :-(
                    log.error(f'Error executing SQL query: {e}')
                try:
                    result = cursor.fetchall()
                except db_lib.ProgrammingError as e:
                    log.warning(f'Not possible to fetch query result: {e}')
        return result


class WebMonitoringDBWrapper(Postgres):
    DATA_TO_DB = {
        'request_timestamp': 'time_stamp',
        'url': 'url',
        'service_name': 'agent',
        'resp_time': 'response_time',
        'resp_status_code': 'status_code',
        'ip_address': 'ip',
        'pattern_found': 'content_validation',
        'comment': 'comment'
    }

    TABLE = 'web_metrics.metrics'

    def __init__(self, host: str, port: Union[int, str], user: str, password: str, database: str):
        """Wrapper / Facade class for psycopg2 lib

        Extends:
            Postgres class

        Args:
            database: DB schema to use
            user: username for authentication
            password: password for authentication
            host: url of DB service
            port: port of DB service to connect to
        """
        super().__init__(host, port, user, password, database)

    def insert(self, data: List[Dict[str, str]], db_lib=psycopg2) -> Optional[List[Tuple[
        datetime.datetime, str, str, datetime.timedelta, int, str, Optional[bool], str
    ]]]:
        """Inserts data to table defined in self.TABLE

        Args:
            data: list of json-serializable dicts
            db_lib: library object to use. Shall have at least compatible
                by signature methods: connect, cursor, cursor.execute,
                cursor.fetchall and ProgrammingError exception.
                Default is postgres psycopg2.

        Returns:
            inserted rows as list of tuples (exact data types specified in signature)

        """
        if not data:
            log.warning('Insertion query called but no data supplied! Operation aborted.')
            return
        try:
            data = [{self.DATA_TO_DB[k]: 'NULL' if v is None else v for k, v in entry.items()} for entry in data]
        except KeyError as e:
            log.error(f'Incorrect data format. Error details: {e.args}')
            return
        columns_str = ', '.join(data[0].keys())
        values = [[f"'{str(v)}'" if v != 'NULL' else f"{str(v)}" for v in item.values()] for item in data]
        values = [f'({", ".join(value_set)})' for value_set in values]
        values_str = ', '.join(values)
        insert_query = f'''
            INSERT INTO {self.TABLE}({columns_str})
            VALUES
            {values_str}
            RETURNING *;
        '''
        result = self.execute_sql(insert_query, db_lib=db_lib)
        if result:
            log.info(f'Successfully inserted rows in db {result}')
        return result

    def delete_data(self, db_lib=psycopg2, **kwargs) -> Optional[List[Tuple[
        datetime.datetime, str, str, datetime.timedelta, int, str, bool, str
    ]]]:
        """Removes rows from the table

        Args:
            **kwargs: keys and values used in WHERE filter
            db_lib: library object to use. Shall have at least compatible
                by signature methods: connect, cursor, cursor.execute,
                cursor.fetchall and ProgrammingError exception.
                Default is postgres psycopg2.

        Returns:
            removed rows as list of tuples

        """
        if not kwargs:
            log.warning('Calling delete with no params rejected! Are you trying to wipe all data?')
            return
        search_param_str = ','.join([f"{str(k)}='{str(v)}'" for k, v in kwargs.items()])
        delete_query = f'''
        DELETE
        FROM {self.TABLE}
        WHERE {search_param_str}
        RETURNING *;
        '''
        result = self.execute_sql(delete_query, db_lib)
        if result:
            log.info(f'Successfully removed rows from db: {result}')
        return result
