from ..llm.llm_builder import LLM
from ...util.db.postgres_vector import PostgresVector
from ...util.db.schema import EmbbedingSchame, DatasetSchema, KB_TABLE_NAME, ANSWER_TABLE_NAME, QUESTION_TABLE_NAME
from ...util.id_generator import generate_common_id
from ...util.logger import logger
import json, re
from scipy.spatial.distance import cosine


class DatasetBuilder:        

    def __init__(self, db_driver: PostgresVector):
        """初始化知识库插件构建器。

        Args:
            connection_params (dict): 数据库连接参数。
        """
        super().__init__()
        self.db_driver = db_driver
        self.db = self.db_driver.db
        self.answer_schema = EmbbedingSchame(ANSWER_TABLE_NAME)
        self.question_schema = EmbbedingSchame(QUESTION_TABLE_NAME)
        self.dataset_schema = DatasetSchema()

    def create_dataset(self, name, creator="gpt_builder"):
        """
        向知识库添加一个新的条目，包括创建者和创建时间。

        Args:
            name (str): 知识库条目的名称。
            creator (str): 条目的创建者。

        Returns:
            int: 新创建的条目的 ID。
        """
        with self.db.cursor() as cursor:
            # 插入新条目并返回生成的 ID
            cursor.execute(f"""
            INSERT INTO {KB_TABLE_NAME} 
            ({self.dataset_schema.name}, {self.dataset_schema.creator}, {self.dataset_schema.created_at}) 
            VALUES (%s, %s, CURRENT_TIMESTAMP) RETURNING {self.dataset_schema.id}
            """, (name, creator))
            
            # 获取并返回新插入条目的 ID
            new_id = cursor.fetchone()[0]
            self.db.commit()  # 确保提交数据库事务以保存插入
            return new_id
            
    def get_dataset(self, filters ,creator="gpt_builder"):
        """
        根据指定的过滤条件获取知识库条目。

        参数:
            creator (str, optional): 创建者的名称。默认为 "gpt_builder"。
            filters (dict): 过滤条件的键值对。

        返回:
            int or None: 如果找到条目，则返回其 ID；否则返回 None。
        """
        # 构建过滤条件的 SQL 语句
        filter_conditions = " AND ".join([f"{key} = %s" for key in filters.keys()])
        filter_values = list(filters.values())

        # 添加 creator 过滤条件
        filter_conditions += f" AND {self.dataset_schema.creator} = %s"
        filter_values.append(creator)

        query = f"""
        SELECT * FROM {KB_TABLE_NAME}
        WHERE {filter_conditions}
        """

        with self.db.cursor() as cursor:
            cursor.execute(query, filter_values)
            result = cursor.fetchall()
            if result:
                return result  # 返回找到的条目
            else:
                return None  # 如果没有找到，返回 None

    def create_datas(self, id, index_text, output_list):
        """向数据库添加一个答案和相关的问题列表。"""
        if not id:
            logger.info("未成功生产知识库实例")
            return
        try:
            # 开启事务
            cursor = self.db.cursor()
            
            # 插入索引并获取ID
            sql_query = self.db_driver.get_insert_into_str(ANSWER_TABLE_NAME, [self.answer_schema.text, self.answer_schema.vector, self.answer_schema.kb_id]) + f" RETURNING {self.answer_schema.id}"
            index_vector = self.generate_vector(index_text).get("embedding")
            if not index_vector:
                logger.info(f"{index_text} 未成功向量化")
                return
            cursor.execute(sql_query, (index_text, index_vector, id))
            index_id = cursor.fetchone()[0]
            logger.info(f"index_id {index_id}")
            
            # 批量插入问题
            question_entries = []
            for question_text in output_list:
                question_vector = self.generate_vector(question_text).get("embedding")
                if question_vector:
                    question_entries.append((index_id, question_text, question_vector))
                else:
                    logger.info(f"{question_text} 未成功向量化")
            
            if question_entries:
                sql_query = self.db_driver.get_insert_into_str(QUESTION_TABLE_NAME, [self.answer_schema.id, self.question_schema.text, self.question_schema.vector]) + f" RETURNING {self.question_schema.id}"
                cursor.executemany(sql_query, question_entries)
            
            self.db.commit()  # 提交事务
            cursor.close()  # 关闭游标
            return True
        except Exception as e:
            logger.error(f"数据库操作失败: {e}")
            self.db.rollback()  # 回滚事务
            cursor.close()  # 关闭游标
            return False
            


    def generate_vector(self, text):
        """生成文本的向量表示，使用spaCy库。

        Args:
            text (str): 输入文本。

        Returns:
            blob: 向量的BLOB表示。
        """
        response = LLM.embedding(text)
        if not response:
            return {}
        return response.get("data",{}).get("data", [])[0] if response.get("data") else {}

    def query_similarity(self, text, dataset_ids=[], similarity=-1, search_all=False):
        """
        计算输入文本与数据库中内容的余弦相似度，并返回包括索引信息和相关内容信息的数据结构。

        Args:
            dataset_ids (list): 知识库ID列表。
            text (str): 查询的文本。
            similarity (float): 用于过滤的相似度阈值。
            search_all (bool): 是否计算加权平均相似度。

        Returns:
            dict: 以知识库ID为键，每个键包含相关内容的列表。
        """
        cursor = self.db.cursor()
        
        if not dataset_ids:
            logger.info("未成功获取知识库实例")
            return None

        input_vector = self.generate_vector(text).get("embedding")
        if not input_vector:
            logger.info("输入文本未成功向量化")
            return None

        kb_content_map = {}

        for kb_id in dataset_ids:
            try:
                # 查询每个kb_id对应的答案和问题数据
                sql = f"""
                    SELECT a.{self.answer_schema.vector}, a.{self.answer_schema.text}, a.{self.answer_schema.id},
                        q.{self.question_schema.vector}, q.{self.question_schema.text}
                    FROM {ANSWER_TABLE_NAME} AS a
                    JOIN {QUESTION_TABLE_NAME} AS q ON a.{self.answer_schema.id} = q.{self.answer_schema.id}
                    WHERE a.{self.answer_schema.kb_id} = %s"""
                logger.info(f"[gpt_builder] SQL:{sql}")
                cursor.execute(sql, (kb_id,))
                data_list = cursor.fetchall()

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

            except Exception as e:
                logger.error(f"处理知识库 {kb_id} 时出错: {e}")

        return kb_content_map

    def query_regex(self, regex, dataset_ids=[]):
        """
        根据正则表达式查询数据库中的内容。

        Args:
            regex (str): 查询的正则表达式。
            dataset_ids (list): 知识库ID列表。

        Returns:
            dict: 以知识库ID为键，每个键包含匹配的索引ID和对应的索引文本及相关内容列表的字典。
        """
        cursor = self.db.cursor()
        if not dataset_ids:
            logger.info("未成功获取知识库实例")
            return None

        # 检查正则表达式是否有效
        try:
            re.compile(regex)
        except re.error as e:
            logger.error(f"无效的正则表达式: {regex}, 错误: {e}")
            return None

        # 最外层字典，以kb_id为键
        kb_content_map = {}

        for kb_id in dataset_ids:
            try:
                # 使用连表查询每个kb_id对应的答案和问题数据
                sql = f"""
                    SELECT a.{self.answer_schema.id} AS answer_id, a.{self.answer_schema.text} AS answer_text, q.{self.question_schema.id} AS question_id, q.{self.question_schema.text} AS question_text
                    FROM {ANSWER_TABLE_NAME} AS a
                    JOIN {QUESTION_TABLE_NAME} AS q ON a.{self.answer_schema.id} = q.{self.answer_schema.id}
                    WHERE a.{self.answer_schema.kb_id} = %s AND q.{self.question_schema.text} ~ %s"""
                logger.info(f"[gpt_builder] SQL:{sql} param {kb_id, regex}")
                cursor.execute(sql, (kb_id, regex))
                data_list = cursor.fetchall()

                for answer_id, answer_text, question_id, question_text in data_list:
                    if kb_id not in kb_content_map:
                        kb_content_map[kb_id] = []

                    # 添加到列表
                    kb_content_map[kb_id].append({
                        "answer_id": answer_id,
                        "answer_text": answer_text,
                        "question_id": question_id,
                        "related_questions": question_text
                    })

            except Exception as e:
                logger.error(f"处理知识库 {kb_id} 时出错: {e}")

        return kb_content_map
        