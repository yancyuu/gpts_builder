import asyncpg
from .db_base import DbBase

class PostgresVectorAsync(DbBase):

    def __init__(self, **kwargs):
        super().__init__()
        self.db = None  # Initialize db connection in an async way
        self.db_params = kwargs

    async def connect_to_db(self):
        """异步使用 asyncpg 连接 PostgreSQL 数据库。"""
        self.db = await asyncpg.connect(
            database=self.db_params['dbname'],
            user=self.db_params['user'],
            password=self.db_params['password'],
            host=self.db_params.get('host', 'localhost'),
            port=self.db_params.get('port', 5432)
        )

    async def get_insert_into_str(self, table_name, columns):
        """
        Construct a SQL INSERT statement dynamically based on input parameters.
        
        Args:
            table_name (str): Name of the table to insert into.
            columns (list): List of column names.

        Returns:
            str: A SQL INSERT statement.
        """
        column_names = ', '.join(columns)
        placeholders = ', '.join(['$' + str(i+1) for i in range(len(columns))])
        return f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"

    async def execute_insert(self, table_name, columns, values):
        """
        Asynchronously insert values into a specified table using given columns and values.

        Args:
            table_name (str): Name of the table.
            columns (list): List of column names.
            values (tuple): Tuple containing the values to insert.

        Returns:
            None
        """
        insert_query = await self.get_insert_into_str(table_name, columns)
        await self.db.execute(insert_query, *values)

    async def close_connection(self):
        """异步关闭 PostgreSQL 数据库连接。"""
        if self.db:
            await self.db.close()
