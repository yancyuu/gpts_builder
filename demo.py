from gpts_builder.builder import LLM
from gpts_builder.session_manager import SessionManager
from gpts_builder.session_manager import SessionManagerAsync
from gpts_builder.session_manager.storage.redis_storage import RedisStorage
from gpts_builder.session_manager.storage.redis_storage_async import RedisStorageAsync

from gpts_builder.builder_async import KbPluginBuilderAsync
from gpts_builder.builder import KbPluginBuilder

from gpts_builder.config import config_manager

from gpts_builder.util.logger import logger
from gpts_builder.util import PostgresVector
from gpts_builder.util import PostgresVectorAsync
import asyncio

config_manager.base_url = "https://www.lazygpt.cn/api"
config_manager.apikey = "lazygpt-B9CzqJP3vbhqH3BF8m0BnMV2A61jdlDaG"

llm = LLM(model="gpt-3.5-turbo")
#session = llm.set_system("你是一个AI助理").set_prompt("测试回复").chat_completions()

# 使用知识库插件，知识库需要一个向量数据库（目前只支持pgvector）
kb = KbPluginBuilder(db_driver=PostgresVector(dbname="postgres", user="username", password="password", host="localhost", port=5432))

#kb_id = kb.add_kb_entry("测试知识库")
#logger.info(kb_id)

# 增加一条知识库内容
# kb.add_index_with_questions(2, "2好知识库", ["2好知识库测试","2好知识库demo"])

# 根据文本在库中查询相似度
# kb_detail = kb.get_kb_by_name(name="测试知识库")
# logger.info(kb_detail)

# s = kb.query_similarity(text="测试", kb_ids=[2, 3])

#logger.info(s)

async def main():
    db_driver = PostgresVectorAsync(dbname="postgres", user="username", password="password", host="localhost", port=5432)
    await db_driver.connect_to_db()  # 确保数据库连接已建立
    
    kb = KbPluginBuilderAsync(db_driver=db_driver)
    
    kb_id = await kb.add_kb_entry("测试知识库")
    print(f"Created KB Entry ID: {kb_id}")
    
    await db_driver.close_connection()  # 关闭数据库连接

if __name__ == "__main__":
    asyncio.run(main())
