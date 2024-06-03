
from gpts_builder.session_manager.storage.redis_storage import RedisStorage
from gpts_builder.session_manager.storage.redis_storage_async import RedisStorageAsync

from gpts_builder.config import config_manager

import asyncio

### 数据检索增强模块测试代码：为什么要做检索增强（https://platform.openai.com/docs/guides/prompt-engineering/strategy-use-external-tools）
config_manager.base_url = "https://www.lazygpt.cn/api"
config_manager.apikey = "lazygpt-B9CzqJP3vbhqH3BF8m0BnMV2A61jdlDaG"


def dataset_demo():
    """
    dataset_demo 检索增强数据集的demo
    """
    from gpts_builder.builder import DatasetBuilder
    from gpts_builder.util import PostgresVector
    # 使用知识库，知识库需要一个向量数据库（目前只支持pgvector）
    ### example1: 初始化向量数据库
    db_driver = PostgresVector(dbname="postgres", user="myuser", password="mypassword", host="localhost", port=5432)
    dataset_builder = DatasetBuilder(db_driver=db_driver)
    dataset_id = dataset_builder.create_dataset("测试知识库")

    ### example2: 根据id获取知识库详情
    dataset_details = dataset_builder.get_dataset(filters={dataset_builder.dataset_schema.id: dataset_id})
    print(f"dataset_details1: {dataset_details}")
    
    ### example3: 根据名称获取知识库详情
    dataset_details = dataset_builder.get_dataset(filters={dataset_builder.dataset_schema.name: "测试知识库"})
    print(f"dataset_details2: {dataset_details}")

    ### example4: 向知识库中增加数据【一个答案（内容）对应多个问题（索引）】
    res = dataset_builder.create_datas(dataset_id, "这是一个答案", ["问题1", "问题2"])
    print(f"datas: {res}")

    ### example5: 根据文本在库中查询相似度
    datas_similarity = dataset_builder.query_similarity(text="这是测试数据", dataset_ids=[1, 2, dataset_id])
    print(f"datas_similarity: {datas_similarity}")

    ### example6: 根据文本在库中正则匹配
    datas_regex = dataset_builder.query_regex(regex=".*问题.*", dataset_ids=[dataset_id])
    print(f"datas_regex: {datas_regex}")

async def dataset_asnyc_demo():
    """
    dataset_asnyc_demo 异步操作知识库模块
    """
    from gpts_builder.builder_async import DatasetBuilderAsync
    from gpts_builder.util import PostgresVectorAsync
    # 使用知识库，知识库需要一个向量数据库（目前只支持pgvector）
    db_driver = PostgresVectorAsync(dbname="postgres", user="myuser", password="mypassword", host="127.0.0.1", port=5432)
    dataset_builder = DatasetBuilderAsync(db_driver=db_driver)
    
    ### example1: 创建知识库
    dataset_id = await dataset_builder.create_dataset("测试知识库")

    ### example2: 通过名称获取知识库详情
    dataset_details = await dataset_builder.get_dataset(filters={dataset_builder.dataset_schema.id: dataset_id})

    ### example3: 根据名称获取知识库详情
    dataset_details = await dataset_builder.get_dataset(filters={dataset_builder.dataset_schema.name: "测试知识库"})
    print(f"dataset_details: {dataset_details}")

    ### example4: 向知识库中增加数据【一个答案（内容）对应多个问题（索引）】
    datas = await dataset_builder.create_datas(dataset_id, "这是一个答案", ["问题1", "问题2"])
    print(f"datas: {datas}")

    ### example5: 根据文本在库中查询相似度
    datas_similarity = await dataset_builder.query_similarity(text="这是测试文本", dataset_ids=[dataset_id])
    print(f"datas_similarity: {datas_similarity}")

    ### example6: 根据文本在库中正则匹配
    datas_regex = await dataset_builder.query_regex(regex="*问题*", dataset_ids=[dataset_id])
    print(f"datas_regex: {datas_regex}")


if __name__ == "__main__":
    #dataset_demo()
    asyncio.run(dataset_asnyc_demo())
