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
from scipy.spatial.distance import cosine
config_manager.base_url = "https://www.lazygpt.cn/api"
config_manager.apikey = "lazygpt-B9CzqJP3vbhqH3BF8m0BnMV2A61jdlDaG"

llm = LLM(model="gpt-3.5-turbo")

# 使用知识库，知识库需要一个向量数据库（目前只支持pgvector）
kb = KbPluginBuilder(db_driver=PostgresVector(dbname="postgres", user="myuser", password="mypassword", host="localhost", port=5432))

kb_id = kb.create_dataset("测试知识库")

# 增加一条知识库内容
kb.create_datas(2, "2好知识库", ["2好知识库测试","2好知识库demo"])

# 根据文本在库中查询相似度
kb_detail = kb.get_kb_by_name(name="测试知识库")
logger.info(kb_detail)

s = kb.query_similarity(text="测试", kb_ids=[2, 3])

logger.info(s)

async def create():
    """
    main 创建知识库
    """
    db_driver = PostgresVectorAsync(dbname="postgres", user="myuser", password="mypassword", host="127.0.0.1", port=5432)
    kb = KbPluginBuilderAsync(db_driver=db_driver)
    
    kb_id = await kb.add_kb_entry("测试知识库")
    logger.info(f"Created KB Entry ID: {kb_id}")
    kb_detail = await kb.get_kb_by_name("测试知识库")
    logger.info(f"kb_detail: {kb_detail}")

    # 增加知识库数据
    await kb.add_index_with_questions(kb_id, "这是一个答案", ["问题1", "问题2"])

async def debug_similarity():
    """
    debug_similarity 测试相似度
    """
    db_driver = PostgresVectorAsync(dbname="postgres", user="myuser", password="mypassword", host="127.0.0.1", port=5432)
    
    
    kb = KbPluginBuilderAsync(db_driver=db_driver)

    # 根据文本相似度查询
    res = await kb.query_similarity("问题2", [kb.get("id") for kb in kb_detail], -1, search_all=False)
    logger.info(f"Similarity: {res}")
    # 根据文本正则查询
    res = await kb.query_regex("这一个问题*", [1,2])
    logger.info(f"Similarity: {res}")


if __name__ == "__main__":
    # 需要测试哪个
    asyncio.run(create())
    # asyncio.run(debug_similarity())
