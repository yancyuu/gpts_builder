from ..llm.llm_async_builder import LLMAsync
from ...util.db.postgres_vector_async import PostgresVectorAsync
from ...util.db.schema import EmbbedingSchame, DatasetSchema, KB_TABLE_NAME, ANSWER_TABLE_NAME, QUESTION_TABLE_NAME
from ...util.id_generator import generate_common_id
from ...util.logger import logger
import json
from scipy.spatial.distance import cosine

class DatasetBuilderAsync:     

    def __init__(self, db_driver: PostgresVectorAsync):
        """初始化知识库插件构建器。"""
        super().__init__()
        self.db_driver = db_driver
        self._connection = None
        self.answer_schema = EmbbedingSchame(ANSWER_TABLE_NAME)
        self.question_schema = EmbbedingSchame(QUESTION_TABLE_NAME)
        self.dataset_schema = DatasetSchema()

    async def create_dataset(self, name, creator="gpt_builder"):
        """向知识库添加一个新的条目，包括创建者和创建时间。"""
        async with (await self.db_driver.pool).acquire() as connection:
            async with connection.transaction():
                sql = f"""
                INSERT INTO {KB_TABLE_NAME} 
                ({self.dataset_schema.name}, {self.dataset_schema.creator}, {self.dataset_schema.created_at}) 
                VALUES ($1, $2, CURRENT_TIMESTAMP) RETURNING {self.dataset_schema.id}
                """
                logger.info(f"Inserting KB entry: {name} by {creator} sql {sql}")
                new_id = await connection.fetchval(sql, name, creator)
            return new_id

    async def get_dataset(self, filters, creator="gpt_builder"):
        """
        异步根据指定的过滤条件获取知识库条目。
        
        参数:
            creator (str, optional): 创建者的名称。默认为 "gpt_builder"。
            filters (dict): 过滤条件的键值对。
        
        返回:
            list: 符合条件的知识库条目列表，每个条目是一个字典。
        """
        # 构建过滤条件的 SQL 语句
        filter_conditions = " AND ".join([f"{key} = ${i+1}" for i, key in enumerate(filters.keys())])
        filter_values = list(filters.values())
        
        # 添加 creator 过滤条件
        filter_conditions += f" AND {self.dataset_schema.creator} = ${len(filters) + 1}"
        filter_values.append(creator)
        
        query = f"""
        SELECT * FROM {KB_TABLE_NAME}
        WHERE {filter_conditions}
        """
        
        async with (await self.db_driver.pool).acquire() as connection:
            async with connection.transaction():
                results = await connection.fetch(query, *filter_values)
        
        return [dict(result) for result in results]

    async def create_datas(self, id, index_text, questions_list):
        """向数据库添加一个答案和相关的问题列表。"""
        if not id:
            logger.info("未成功生产知识库实例")
            return
        async with (await self.db_driver.pool).acquire() as connection:
            async with connection.transaction():
                try:
                    # 插入索引并获取ID
                    sql_query = self.db_driver.get_insert_into_str(ANSWER_TABLE_NAME, [self.answer_schema.text, self.answer_schema.vector, self.answer_schema.kb_id]) + f" RETURNING {self.answer_schema.id}"
                    logger.info(f"sql_query {sql_query}")
                    index_vector = await self.generate_vector(index_text)
                    if not index_vector:
                        logger.info(f"{index_text} 未成功向量化")
                        return
                    index_vector = json.dumps(index_vector)
                    index_id = await connection.fetchval(
                        sql_query,
                        index_text, index_vector, id
                    )
                    logger.info(f"index_id {index_id}")
                    # 批量插入问题
                    question_entries = []
                    for question_text in questions_list:
                        question_vector = await self.generate_vector(question_text)
                        if question_vector:
                            question_vector = json.dumps(question_vector)
                            question_entries.append((index_id, question_text, question_vector))
                        else:
                            logger.info(f"{question_text} 未成功向量化")
                        
                    if question_entries:
                        sql_query = self.db_driver.get_insert_into_str(QUESTION_TABLE_NAME, [self.answer_schema.id, self.question_schema.text, self.question_schema.vector]) + f" RETURNING {self.question_schema.id}"
                        await connection.executemany(sql_query,question_entries)
                except Exception as e:
                    logger.error(f"数据库操作失败: {e}")
                    # 事务回滚是自动的，但仍可以记录或处理异常
                    raise


    async def generate_vector(self, text):
        """生成文本的向量表示，使用spaCy库。

        Args:
            text (str): 输入文本。

        Returns:
            blob: 向量的BLOB表示。
        """
        response = await LLMAsync.embedding(text)
        if not response:
            return {}
        embedding = response.get("data",{}).get("data", [])[0] if response.get("data") else {}
        if not embedding and embedding.get("embedding"):
            return
        return embedding.get("embedding")

    async def query_similarity(self, text, dataset_ids=[], similarity=-1, search_all=False):
        """
        使用联合查询来计算输入文本与数据库中内容的余弦相似度，并返回相关信息。

        Args:
            dataset_ids (list): 知识库ID列表。
            text (str): 查询的文本。
            similarity (float): 用于过滤的相似度阈值。
            search_all (bool): 是否计算加权平均相似度。

        Returns:
            dict: 以知识库ID为键，每个键包含相关内容的列表。
        """
        if not dataset_ids:
            logger.info("未成功获取知识库实例")
            return None

        input_vector = await self.generate_vector(text)
        if not input_vector:
            logger.info("输入文本未成功向量化")
            return None

        kb_content_map = {}
        async with (await self.db_driver.pool).acquire() as connection:
            async with connection.transaction():
                for dataset_id in dataset_ids:
                    sql = f"""
                        SELECT a.{self.answer_schema.vector}, a.{self.answer_schema.text}, a.{self.answer_schema.id},
                            q.{self.question_schema.vector}, q.{self.question_schema.text}
                        FROM {ANSWER_TABLE_NAME} AS a
                        JOIN {QUESTION_TABLE_NAME} AS q ON a.{self.answer_schema.id} = q.{self.answer_schema.id}
                        WHERE a.{self.answer_schema.kb_id} = $1"""
                    logger.info(f"[gpt_builder] SQL:{sql}")
                    data_list = await connection.fetch(sql, dataset_id)

                    content_list = []
                    for answer_vector, answer_text, answer_id, question_vector, question_text in data_list:
                        answer_vector_data = json.loads(answer_vector)
                        question_vector_data = json.loads(question_vector)
                        answer_similarity = 1 - cosine(input_vector, answer_vector_data)
                        question_similarity = 1 - cosine(input_vector, question_vector_data)
                        total_similarity = (answer_similarity + question_similarity) / 2 if search_all else question_similarity

                        if total_similarity < similarity:
                            continue

                        content_list.append({
                            "index_id": answer_id,
                            "related_questions": question_text,
                            "answer_text": answer_text,
                            "similarity": total_similarity,
                            "search_all": search_all
                        })

                    if content_list:
                        content_list.sort(key=lambda x: x['similarity'], reverse=True)
                        kb_content_map[dataset_id] = content_list
        return kb_content_map
    
    async def query_regex(self, regex, dataset_ids=[]):
        """
        根据正则表达式查询数据库中符合条件的答案索引。

        Args:
            regex (str): 查询的正则表达式。
            dataset_ids (list): 知识库ID列表。

        Returns:
            dict: 以知识库ID为键，每个键包含匹配的索引ID和对应的索引文本及相关内容列表的字典。
        """

        if not dataset_ids:
            logger.info("未成功获取知识库实例")
            return None

        # 最外层字典，以kb_id为键
        kb_content_map = {}
        async with (await self.db_driver.pool).acquire() as connection:
            async with connection.transaction():
                for kb_id in dataset_ids:
                    # 使用连表查询每个kb_id对应的答案和问题数据
                    sql = f"""
                        SELECT a.{self.answer_schema.id} AS answer_id, a.{self.answer_schema.text} AS answer_text,
                            q.{self.question_schema.id} AS question_id, q.{self.question_schema.text} AS question_text
                        FROM {ANSWER_TABLE_NAME} AS a
                        JOIN {QUESTION_TABLE_NAME} AS q ON a.{self.answer_schema.id} = q.{self.answer_schema.id}
                        WHERE a.{self.answer_schema.kb_id} = %s AND q.{self.question_schema.text} ~ %s"""
                    data_list = await connection.fetch(sql, kb_id, regex)

                    for question_text, question_id, answer_id, answer_text in data_list:
                        if kb_id not in kb_content_map:
                            kb_content_map[kb_id] = []

                        # 添加到列表
                        kb_content_map[kb_id].append({
                            "answer_id": answer_id,
                            "related_answer": answer_text,
                            "question_id": question_id,
                            "questions_text": question_text
                        })

        return kb_content_map



