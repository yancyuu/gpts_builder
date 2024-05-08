import psycopg2
from .db_base import DbBase

class PostgresVector(DbBase):


    def __init__(self, **args):
        super().__init__()
        self.db = self.connect_to_db(**args)
    
    def connect_to_db(self, dbname, user, password, host="localhost", port=5432):
        """使用 psycopg2 连接 PostgreSQL 数据库。"""
        return psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
    
    def get_insert_into_str(self, table_name, columns):
        """
        Insert values into a specified table with given columns.

        Args:
        - table_name: Name of the table to insert into.
        - columns: List of column names.
        - values: List of tuples containing the values to insert.

        Returns:
        - None
        """
        # Construct the SQL INSERT statement dynamically based on input parameters
        column_names = ', '.join(columns)
        placeholders = ', '.join(['%s' for _ in columns])
        return f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})" 

    def close_connection(self):
        """关闭 PostgreSQL 数据库连接。"""
        if self.db:
            self.db.close()
