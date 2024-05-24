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
        self._connection = None
        self.answer_schema = EmbbedingSchame(ANSWER_TABLE_NAME)
        self.question_schema = EmbbedingSchame(QUESTION_TABLE_NAME)
        self.kb_schema = KbSchame()

    async def add_kb_entry(self, name, creator="gpt_builder"):
        """向知识库添加一个新的条目，包括创建者和创建时间。"""
        async with (await self.db_driver.pool).acquire() as connection:
            async with connection.transaction():
                sql = f"""
                INSERT INTO {KB_TABLE_NAME} 
                ({self.kb_schema.name}, {self.kb_schema.creator}, {self.kb_schema.created_at}) 
                VALUES ($1, $2, CURRENT_TIMESTAMP) RETURNING {self.kb_schema.id}
                """
                logger.info(f"Inserting KB entry: {name} by {creator} sql {sql}")
                new_id = await connection.fetchval(sql, name, creator)
            return new_id

    async def get_kb_by_name(self, name, creator="gpt_builder"):
        """异步根据名称获取知识库条目的 ID。"""
        async with (await self.db_driver.pool).acquire() as connection:
            async with connection.transaction():
                # 查询知识库中是否存在指定名称的条目，并获取其 ID
                results = await connection.fetch(f"""
                SELECT * FROM {KB_TABLE_NAME}
                WHERE {self.kb_schema.name} = $1 AND {self.kb_schema.creator} = $2
                """, name, creator)
        return [dict(result) for result in results]

    async def add_index_with_questions(self, id, index_text, questions_list):
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


    async def query_similarity(self, text, kb_ids=[], similarity=-1, search_all=False):
        """
        使用联合查询来计算输入文本与数据库中内容的余弦相似度，并返回相关信息。

        Args:
            kb_ids (list): 知识库ID列表。
            text (str): 查询的文本。
            similarity (float): 用于过滤的相似度阈值。
            search_all (bool): 是否计算加权平均相似度。

        Returns:
            dict: 以知识库ID为键，每个键包含相关内容的列表。
        """
        if not kb_ids:
            logger.info("未成功获取知识库实例")
            return None

        input_vector = await self.generate_vector(text)
        if not input_vector:
            logger.info("输入文本未成功向量化")
            return None

        kb_content_map = {}
        async with (await self.db_driver.pool).acquire() as connection:
            async with connection.transaction():
                for kb_id in kb_ids:
                    sql = f"""
                        SELECT a.{self.answer_schema.vector}, a.{self.answer_schema.text}, a.{self.answer_schema.id},
                            q.{self.question_schema.vector}, q.{self.question_schema.text}
                        FROM {ANSWER_TABLE_NAME} AS a
                        JOIN {QUESTION_TABLE_NAME} AS q ON a.{self.answer_schema.id} = q.{self.answer_schema.id}
                        WHERE a.{self.answer_schema.kb_id} = $1"""
                    data_list = await connection.fetch(sql, kb_id)

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
                        kb_content_map[kb_id] = content_list
        return kb_content_map
    
    async def query_regex(self, regex, kb_ids=[]):
        """
        根据正则表达式查询数据库中的内容。

        Args:
            regex (str): 查询的正则表达式。
            kb_ids (list): 知识库ID列表。

        Returns:
            dict: 以知识库ID为键，每个键包含匹配的索引ID和对应的索引文本及相关内容列表的字典。
        """

        if not kb_ids:
            logger.info("未成功获取知识库实例")
            return None

        # 最外层字典，以kb_id为键
        kb_content_map = {}
        async with (await self.db_driver.pool).acquire() as connection:
            async with connection.transaction():
                for kb_id in kb_ids:
                    # 查询每个kb_id对应的答案数据
                    sql = f"""
                        SELECT {self.answer_schema.id}, {self.answer_schema.text}
                        FROM {ANSWER_TABLE_NAME}
                        WHERE {self.answer_schema.kb_id} = $1 AND {self.answer_schema.text} ~ $2"""
                    answer_data_list = await connection.fetch(sql, kb_id, regex)

                    for answer_id, answer_text in answer_data_list:
                        # 查询与答案ID关联的所有问题
                        sql = f"""
                            SELECT {self.question_schema.text}
                            FROM {QUESTION_TABLE_NAME}
                            WHERE {self.answer_schema.id} = $1"""
                        question_texts = await connection.fetch(sql, answer_id)
                        questions = [question[self.question_schema.text] for question in question_texts]

                        if kb_id not in kb_content_map:
                            kb_content_map[kb_id] = []

                        # 添加到列表
                        kb_content_map[kb_id].append({
                            "answer_id": answer_id,
                            "answer_text": answer_text,
                            "related_questions": questions
                        })

        return kb_content_map



