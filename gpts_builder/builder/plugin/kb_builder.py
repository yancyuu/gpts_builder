from ..llm.llm_builder import LLM
from ...util.db.postgres_vector import PostgresVector
from ...util.db.schema import EmbbedingSchame, KbSchame, KB_TABLE_NAME, ANSWER_TABLE_NAME, QUESTION_TABLE_NAME
from ...util.id_generator import generate_common_id
from ...util.logger import logger
import json
from scipy.spatial.distance import cosine


class KbPluginBuilder:        

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
        self.kb_schema = KbSchame()
        # 初始化表格
        self.create_tables()
    
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
                {self.kb_schema.id} SERIAL PRIMARY KEY,
                {self.kb_schema.name} TEXT
            )""")

            # 创建索引表 index_table，关联到 kb 表的 id
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {ANSWER_TABLE_NAME} (
                {self.answer_schema.id} SERIAL PRIMARY KEY,
                {self.answer_schema.text} TEXT,
                {self.answer_schema.vector} vector,
                {self.answer_schema.kb_id} INTEGER,
                FOREIGN KEY ({self.answer_schema.kb_id}) REFERENCES {KB_TABLE_NAME} ({self.kb_schema.id})
            )""")

            # 创建内容表 content_table，关联到 index_table 表的 id
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {QUESTION_TABLE_NAME} (
                {self.question_schema.id} SERIAL PRIMARY KEY,
                {self.answer_schema.id} INTEGER,
                {self.question_schema.text} TEXT,
                {self.question_schema.vector} vector,
                FOREIGN KEY ({self.answer_schema.id}) REFERENCES {ANSWER_TABLE_NAME} ({self.answer_schema.id})
            )""")

            # 提交所有更改
            self.db.commit()

    def add_kb_entry(self, name, creator="gpt_builder"):
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
            ({self.kb_schema.name}, {self.kb_schema.creator}, {self.kb_schema.created_at}) 
            VALUES (%s, %s, CURRENT_TIMESTAMP) RETURNING {self.kb_schema.id}
            """, (name, creator))
            
            # 获取并返回新插入条目的 ID
            new_id = cursor.fetchone()[0]
            self.db.commit()  # 确保提交数据库事务以保存插入
            return new_id

        
    def get_kb_by_name(self, name):
        """
        根据名称获取知识库条目的 ID。

        Args:
            name (str): 知识库条目的名称。

        Returns:
            int or None: 如果找到条目，则返回其 ID；否则返回 None。
        """
        with self.db.cursor() as cursor:
            # 查询知识库中是否存在指定名称的条目，并获取其 ID
            cursor.execute(f"""
            SELECT {self.kb_schema.id} FROM {KB_TABLE_NAME}
            WHERE {self.kb_schema.name} = %s
            """, (name,))
            
            result = cursor.fetchone()
            if result:
                return result[0]  # 返回找到的条目 ID
            else:
                return None  # 如果没有找到，返回 None

    def add_index_with_questions(self, id, index_text, questions_list):
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
            for question_text in questions_list:
                question_vector = self.generate_vector(question_text).get("embedding")
                if question_vector:
                    question_entries.append((index_id, question_text, question_vector))
                else:
                    logger.info(f"{question_text} 未成功向量化")
            
            if question_entries:
                sql_query = self.db_driver.get_insert_into_str(QUESTION_TABLE_NAME, [self.answer_schema.id, self.question_schema.text, self.question_schema.vector]) + f" RETURNING {self.question_schema.id}"
                cursor.executemany(sql_query, question_entries)
            
            self.db.commit()  # 提交事务
        except Exception as e:
            logger.error(f"数据库操作失败: {e}")
            self.db.rollback()  # 回滚事务
        finally:
            cursor.close()  # 关闭游标


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

    def query_similarity(self, text, kb_ids=[], approximation_filter={"index": -1, "content": -1}):
        """
        计算输入文本与数据库中内容的余弦相似度，并返回包括索引信息和相关内容信息的数据结构。

        Args:
            kb_ids (list): 知识库ID列表。
            text (str): 查询的文本。
            approximation_filter (dict): 用于过滤的相似度阈值，包括索引和内容。

        Returns:
            dict: 以知识库ID为键，每个键包含索引ID和对应索引文本及相关内容列表的字典。
        """
        cursor = self.db.cursor()
        
        if not kb_ids:
            logger.info("未成功获取知识库实例")
            return None

        input_vector = self.generate_vector(text).get("embedding")
        if not input_vector:
            logger.info("输入文本未成功向量化")
            return None

        # 最外层字典，以kb_id为键
        kb_content_map = {}

        for kb_id in kb_ids:
            # 查询每个kb_id对应的索引数据
            cursor.execute(f"""
                SELECT {self.answer_schema.vector}, {self.answer_schema.text}, {self.answer_schema.id}
                FROM {ANSWER_TABLE_NAME}
                WHERE {self.answer_schema.kb_id} = %s""", (kb_id,))
            index_data_list = cursor.fetchall()

            index_content = {}  # 存储当前kb_id下的索引和内容
            for index_vector, index_text, index_id in index_data_list:
                try:
                    index_vector_data = json.loads(index_vector)
                    index_similarity = 1 - cosine(input_vector, index_vector_data)

                    # 过滤索引的相似度
                    if index_similarity < approximation_filter.get("index", -1):
                        continue

                    # 查询与索引ID关联的所有内容
                    cursor.execute(f"""
                        SELECT {self.question_schema.vector}, {self.question_schema.text}
                        FROM {QUESTION_TABLE_NAME}
                        WHERE {self.answer_schema.id} = %s""", (index_id,))
                    content_data = cursor.fetchall()

                    content_list = []
                    for content_vector, content_text in content_data:
                        content_vector_data = json.loads(content_vector)
                        content_similarity = 1 - cosine(input_vector, content_vector_data)

                        # 过滤内容的相似度
                        if content_similarity < approximation_filter.get("content", -1):
                            continue

                        content_list.append({'text': content_text, 'similarity': content_similarity})

                    # 按相似度分数降序排序
                    content_list.sort(key=lambda x: x['similarity'], reverse=True)

                    # 保存索引和对应的内容
                    index_content = {
                        "index_id": index_id,
                        'index_text': index_text,
                        'index_similarity': index_similarity,
                        'contents': content_list
                    }
                except Exception as e:
                    logger.error(f"处理索引 {index_id} 时出错: {e}")
            
            kb_content_map[kb_id] = index_content

        return kb_content_map
