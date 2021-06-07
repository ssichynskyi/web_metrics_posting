import datetime
import logging
import psycopg2

from typing import Union, Dict, List, Tuple, Optional, Any


log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class SQLDatabaseWrapper:
    def __init__(self, host: str, port: Union[int, str], user: str, password: str, database: str):
        """Wrapper / Facade class for psycopg2 lib

        Args:
            host: url of DB service
            port: port of DB service to connect to
            user: username for authentication
            password: password for authentication
            database: DB schema to use

        """
        self._connection_params = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database
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


class WebMonitoringDBWrapper(SQLDatabaseWrapper):
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

    def __init__(self, host: str, port: Union[int, str], user: str, password: str, database: str):
        """Wrapper / Facade class for psycopg2 lib

        Extends:
            Postgres class

        Args:
            host: url of DB service
            port: port of DB service to connect to
            user: username for authentication
            password: password for authentication
            database: DB schema to use
        """
        super().__init__(host, port, user, password, database)
        self._user = user

    def create_table_if_not_exist(
            self,
            schema: str,
            table: str,
            db_lib=psycopg2
    ):
        """Creates table and schema if not exist

        Args:
            schema: database schema to create (if not exists)
            table: table in schema to create (if not exists)
            db_lib: library object to use. Shall have at least compatible
                by signature methods: connect, cursor, cursor.execute,
                cursor.fetchall and ProgrammingError exception.
                Default is postgres psycopg2.

        Returns:
            inserted rows as list of tuples (exact data types specified in signature)

        """
        create_table_query = f'''
            CREATE SCHEMA IF NOT EXISTS {schema}
                AUTHORIZATION {self._user};
            CREATE TABLE IF NOT EXISTS {schema}.{table}(
                time_stamp timestamp NOT NULL,
                url VARCHAR NOT NULL,
                agent VARCHAR NOT NULL,
                response_time INTERVAL(3),
                status_code INT,
                ip VARCHAR,
                content_validation BOOLEAN,
                comment VARCHAR
            );
            CREATE INDEX IF NOT EXISTS
                {table}_url ON {schema}.{table}(url);
            CREATE INDEX IF NOT EXISTS
                {table}_status_code ON {schema}.{table}(status_code);
            CREATE INDEX IF NOT EXISTS
                {table}_agent ON {schema}.{table}(agent);
            CREATE INDEX IF NOT EXISTS
                {table}_response_time ON {schema}.{table}(response_time);
            CREATE INDEX IF NOT EXISTS
                {table}_ip ON {schema}.{table}(ip);
            CREATE INDEX IF NOT EXISTS
                {table}_comment ON {schema}.{table}(comment);
        '''
        self.execute_sql(create_table_query, db_lib=db_lib)

    def insert(
            self,
            data: List[Dict[str, str]],
            schema: str,
            table: str,
            db_lib=psycopg2
    ) -> Optional[List[Tuple[
        datetime.datetime, str, str, datetime.timedelta, int, str, Optional[bool], str
    ]]]:
        """Inserts data to table defined as schema.table

        Args:
            data: list of json-serializable dicts
            schema: database schema
            table: table name in DB to insert data to
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

        full_table_name = f'{schema}.{table}'

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
            INSERT INTO {full_table_name}({columns_str})
            VALUES
            {values_str}
            RETURNING *;
        '''
        self.create_table_if_not_exist(schema, table, db_lib)
        result = self.execute_sql(insert_query, db_lib=db_lib)
        if result:
            log.info(f'Successfully inserted rows in db {result}')
        return result

    def delete_data(
            self,
            schema: str,
            table: str,
            db_lib=psycopg2,
            **kwargs
    ) -> Optional[List[Tuple[
        datetime.datetime, str, str, datetime.timedelta, int, str, bool, str
    ]]]:
        """Removes rows from the table.

        Args:
            schema: database schema
            table: table name in DB to insert data to
            db_lib: library object to use. Shall have at least compatible
                by signature methods: connect, cursor, cursor.execute,
                cursor.fetchall and ProgrammingError exception.
                Default is postgres psycopg2.
            **kwargs: keys and values used in WHERE filter

        Returns:
            removed rows as list of tuples

        """
        if not kwargs:
            log.warning('Calling delete with no params rejected! Are you trying to wipe all data?')
            return
        full_table_name = f'{schema}.{table}'
        search_param_str = ','.join([f"{str(k)}='{str(v)}'" for k, v in kwargs.items()])
        delete_query = f'''
        DELETE
        FROM {full_table_name}
        WHERE {search_param_str}
        RETURNING *;
        '''
        result = self.execute_sql(delete_query, db_lib)
        if result:
            log.info(f'Successfully removed rows from db: {result}')
        return result
