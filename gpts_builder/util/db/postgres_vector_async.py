from asyncpg import create_pool
from asyncio import get_event_loop
from .db_base import DbBase
from ...util.db.schema import EmbbedingSchame, KbSchame, KB_TABLE_NAME, ANSWER_TABLE_NAME, QUESTION_TABLE_NAME


class PostgresVectorAsync(DbBase):

    @property
    async def pool(self):
        if self._pool is None:
            await self.init_db()
        return self._pool

    def __init__(self, **kwargs):
        super().__init__()
        self.db = None  # Initialize db connection in an async way
        self._pool = None
        self.db_params = kwargs
        self.answer_schema = EmbbedingSchame(ANSWER_TABLE_NAME)
        self.question_schema = EmbbedingSchame(QUESTION_TABLE_NAME)
        self.kb_schema = KbSchame()

    async def init_db(self):
        """初始化数据库连接池。"""
        self._pool = await create_pool(
            database=self.db_params['dbname'],
            user=self.db_params['user'],
            password=self.db_params['password'],
            host=self.db_params.get('host', 'localhost'),
            port=self.db_params.get('port', 5432),
            min_size=1,
            max_size=10
        )
        await self.create_tables()
    
    async def create_tables(self):
        """异步创建 PostgreSQL 表格，包括知识库表以及支持 pgvector 的索引和内容表格。"""
        async with (await self.pool).acquire() as connection:
            async with connection.transaction():
                await connection.execute("""
                CREATE EXTENSION IF NOT EXISTS vector;  -- 确保 pgvector 扩展已安装
                """)
                # 创建知识库表 kb
                await connection.execute(f"""
                CREATE TABLE IF NOT EXISTS {KB_TABLE_NAME} (
                    {self.kb_schema.id} SERIAL PRIMARY KEY,
                    {self.kb_schema.name} TEXT,
                    {self.kb_schema.creator} TEXT,
                    {self.kb_schema.created_at} TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")
                # 创建索引表 answer_table
                await connection.execute(f"""
                CREATE TABLE IF NOT EXISTS {ANSWER_TABLE_NAME} (
                    {self.answer_schema.id} SERIAL PRIMARY KEY,
                    {self.answer_schema.text} TEXT,
                    {self.answer_schema.vector} vector,
                    {self.answer_schema.kb_id} INTEGER,
                    {self.answer_schema.created_at} TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY ({self.answer_schema.kb_id}) REFERENCES {KB_TABLE_NAME} ({self.kb_schema.id})
                )""")
                # 创建内容表 question_table
                await connection.execute(f"""
                CREATE TABLE IF NOT EXISTS {QUESTION_TABLE_NAME} (
                    {self.question_schema.id} SERIAL PRIMARY KEY,
                    {self.answer_schema.id} INTEGER,
                    {self.question_schema.text} TEXT,
                    {self.question_schema.vector} vector,
                    {self.question_schema.created_at} TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY ({self.answer_schema.id}) REFERENCES {ANSWER_TABLE_NAME} ({self.answer_schema.id})
                )""")

    def get_insert_into_str(self, table_name, columns):
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
