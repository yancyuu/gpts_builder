
class DbBase:

    def connect_to_db(self):
        """连接数据库，由子类实现具体的连接方式。"""
        raise NotImplementedError("Subclasses must implement this method")

    def create_tables(self):
        """创建数据库表，由子类实现具体的建表语句。"""
        raise NotImplementedError("Subclasses must implement this method")

    def close_connection(self):
        """关闭数据库连接，由子类实现具体的关闭方法。"""
        raise NotImplementedError("Subclasses must implement this method")
