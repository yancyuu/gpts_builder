import psycopg2
from .db_base import DbBase
from ...util.db.schema import EmbbedingSchame, DatasetSchema, KB_TABLE_NAME, ANSWER_TABLE_NAME, QUESTION_TABLE_NAME


class PostgresVector(DbBase):


    def __init__(self, **args):
        super().__init__()
        self.db = self.connect_to_db(**args)
        self.answer_schema = EmbbedingSchame(ANSWER_TABLE_NAME)
        self.question_schema = EmbbedingSchame(QUESTION_TABLE_NAME)
        self.dataset_schema = DatasetSchema()
        self.create_tables()
    
    def connect_to_db(self, dbname, user, password, host="localhost", port=5432):
        """使用 psycopg2 连接 PostgreSQL 数据库。"""
        return psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
    
    def create_tables(self):
        """创建 PostgreSQL 表格，包括知识库表以及支持 pgvector 的索引和内容表格。"""
        with self.db.cursor() as cursor:
            # 创建扩展，如果尚未创建
            cursor.execute("""
            CREATE EXTENSION IF NOT EXISTS vector;  -- 确保 pgvector 扩展已安装
            """)

            # 创建知识库表 kb
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {KB_TABLE_NAME} (
                {self.dataset_schema.id} SERIAL PRIMARY KEY,
                {self.dataset_schema.name} TEXT,
                {self.dataset_schema.creator} TEXT,
                {self.dataset_schema.created_at} TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")

            # 创建索引表 index_table，关联到 kb 表的 id
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {ANSWER_TABLE_NAME} (
                {self.answer_schema.id} SERIAL PRIMARY KEY,
                {self.answer_schema.text} TEXT,
                {self.answer_schema.vector} vector,
                {self.answer_schema.kb_id} INTEGER,
                {self.answer_schema.created_at} TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY ({self.answer_schema.kb_id}) REFERENCES {KB_TABLE_NAME} ({self.dataset_schema.id})
            )""")

            # 创建内容表 content_table，关联到 index_table 表的 id
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {QUESTION_TABLE_NAME} (
                {self.question_schema.id} SERIAL PRIMARY KEY,
                {self.answer_schema.id} INTEGER,
                {self.question_schema.text} TEXT,
                {self.question_schema.vector} vector,
                {self.question_schema.created_at} TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY ({self.answer_schema.id}) REFERENCES {ANSWER_TABLE_NAME} ({self.answer_schema.id})
            )""")

            # 提交所有更改
            self.db.commit()
    
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
