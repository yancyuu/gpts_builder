from ..llm.llm_async_builder import LLMAsync
from ...util.db.postgres_vector_async import PostgresVectorAsync
from ...util.db.schema import EmbbedingSchame, KbSchame, KB_TABLE_NAME, ANSWER_TABLE_NAME, QUESTION_TABLE_NAME
from ...util.id_generator import generate_common_id
from ...util.logger import logger
import json
from scipy.spatial.distance import cosine

class KbPluginBuilderAsync:        

    def __init__(self, db_driver: PostgresVectorAsync):
        """初始化知识库插件构建器。"""
        super().__init__()
        self.db_driver = db_driver
        self.answer_schema = EmbbedingSchame(ANSWER_TABLE_NAME)
        self.question_schema = EmbbedingSchame(QUESTION_TABLE_NAME)
        self.kb_schema = KbSchame()
    
    async def create_tables(self):
        """异步创建 PostgreSQL 表格，包括知识库表以及支持 pgvector 的索引和内容表格。"""
        async with self.db_driver.db.acquire() as connection:
            async with connection.transaction():
                await connection.execute("""
                CREATE EXTENSION IF NOT EXISTS vector;  -- 确保 pgvector 扩展已安装
                """)

                # 创建知识库表 kb
                await connection.execute(f"""
                CREATE TABLE IF NOT EXISTS {KB_TABLE_NAME} (
                    {self.kb_schema.id} SERIAL PRIMARY KEY,
                    {self.kb_schema.name} TEXT
                )""")

                # 创建索引表 answer_table
                await connection.execute(f"""
                CREATE TABLE IF NOT EXISTS {ANSWER_TABLE_NAME} (
                    {self.answer_schema.id} SERIAL PRIMARY KEY,
                    {self.answer_schema.text} TEXT,
                    {self.answer_schema.vector} vector,
                    {self.answer_schema.kb_id} INTEGER,
                    FOREIGN KEY ({self.answer_schema.kb_id}) REFERENCES {KB_TABLE_NAME} ({self.kb_schema.id})
                )""")

                # 创建内容表 question_table
                await connection.execute(f"""
                CREATE TABLE IF NOT EXISTS {QUESTION_TABLE_NAME} (
                    {self.question_schema.id} SERIAL PRIMARY KEY,
                    {self.answer_schema.id} INTEGER,
                    {self.question_schema.text} TEXT,
                    {self.question_schema.vector} vector,
                    FOREIGN KEY ({self.answer_schema.id}) REFERENCES {ANSWER_TABLE_NAME} ({self.answer_schema.id})
                )""")

    async def add_kb_entry(self, name, creator="gpt_builder"):
        """向知识库添加一个新的条目，包括创建者和创建时间。"""
        # 使用 self.db_driver.db 直接作为连接使用
        async with self.db_driver.db.transaction():
            result = await self.db_driver.db.execute(f"""
            INSERT INTO {KB_TABLE_NAME} 
            ({self.kb_schema.name}, {self.kb_schema.creator}, {self.kb_schema.created_at}) 
            VALUES ($1, $2, CURRENT_TIMESTAMP) RETURNING {self.kb_schema.id}
            """, name, creator)
            
            # 获取并返回新插入条目的 ID
            new_id = await self.db_driver.db.fetchval(result)
            return new_id

    async def get_kb_by_name(self, name):
        """异步根据名称获取知识库条目的 ID。"""
        async with self.db_driver.db.acquire() as connection:
            # 查询知识库中是否存在指定名称的条目，并获取其 ID
            result = await connection.fetchrow(f"""
            SELECT {self.kb_schema.id} FROM {KB_TABLE_NAME}
            WHERE {self.kb_schema.name} = $1
            """, name)
            
            if result:
                return result['id']
            else:
                return None

# Note: Add other methods similarly adjusted for async operations.
