#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2022/6/4 下午6:28
# @Author  : Samge
from abc import abstractmethod
import pymysql
import logging

class BaseMySql(object):

    conn = None
    cursor = None

    def __init__(self, host=None, user=None, password=None, database=None, port=None):
        self.logger = logging.getLogger(__name__)
        host = host or self.get_default_host()
        user = user or self.get_default_user()
        password = password or self.get_default_password()
        database = database or self.get_default_database()
        port = int(port or self.get_default_port() or 0)
        self.i('{} {} {} {}'.format(host, user, database, port))
        try:
            self.conn = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=port
            )
            self.cursor = self.conn.cursor()
            
            # 设置事务隔离级别为“读已提交”（Read Committed），避免长连接模式下无法读取到最新数据
            self.cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
            self.conn.commit()

        except Exception as e:
            self.e(e)
            pass

    def query_list(self, sql: str) -> list:
        """
        有返回值的sql执行
        :param sql:
        :return: 字典列表
        """
        try:
            # 检查连接是否断开，如果断开就进行重连
            self.conn.ping(reconnect=True)
            cur = self.cursor
            cur.execute(sql)
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, self.parse_encoding(row))) for row in cur.fetchall()]
        except Exception as e:
            self.e(e)
            return []

    def execute(self, sql: str) -> bool:
        """
        无返回的sql执行
        :param sql:
        :return: True=执行成功, False=执行失败
        """
        try:
            self.conn.ping(reconnect=True)
            cur = self.cursor
            cur.execute(sql)
            self.conn.commit()
            return True
        except Exception as e:
            self.e(e)
            return False

    def parse_encoding(self, row) -> list:
        """处理window中查询出来的中文乱码问题"""
        row = list(row)
        try:
            for i in range(len(row)):
                item = row[i]
                if type(item) is str:
                    row[i] = item.encode('latin1').decode('gbk')
        except Exception as e:
            # self.e(e)
            pass
        return row

    def close_connect(self) -> None:
        """关闭游标和连接"""
        try:
            self.cursor.close()
            self.conn.close()
            self.child_close()
            self.i('释放数据库连接')
        except Exception as e:
            self.e(e)

    def child_close(self) -> None:
        """
        提供给子类处理的关闭操作
        """
        pass

    def _need_update(self, spider) -> bool:
        """
        判断该爬虫是否需要进行更新操作
        :param spider:
        :return:
        """
        try:
            if not spider or not hasattr(spider, 'NEED_UPDATE'):
                return False
            self.i(f"是否需要进行更新 spider.NEED_UPDATE={spider.NEED_UPDATE}")
            return spider.NEED_UPDATE
        except:
            return False

    def _get_update_field_list(self, spider) -> list:
        """
        获取需要指定更新的字段
        :param spider:
        :return:
        """
        try:
            if not spider or not hasattr(spider, 'UPDATE_FIELD_LIST'):
                return []
            self.i(f"指定更新字段 spider.UPDATE_FIELD_LIST={spider.UPDATE_FIELD_LIST}")
            return spider.UPDATE_FIELD_LIST
        except:
            return []
        
    def i(self, msg):
        self.logger.info(msg)
        
    def e(self, msg):
        self.logger.error(msg)

    @abstractmethod
    def get_default_host(self):
        """
        获取实际的 默认数据库连接地址

        （子类必须实现该方法）
        """
        raise self.get_error_tip()

    @abstractmethod
    def get_default_user(self):
        """
        获取实际的 默认数据库连接用户名

        （子类必须实现该方法）
        """
        raise self.get_error_tip()

    @abstractmethod
    def get_default_password(self):
        """
        获取实际的 默认数据库连接用户密码

        （子类必须实现该方法）
        """
        raise self.get_error_tip()

    @abstractmethod
    def get_default_database(self):
        """
        获取实际的 默认数据库连接操作的数据库

        （子类必须实现该方法）
        """
        raise self.get_error_tip()

    @abstractmethod
    def get_default_port(self):
        """
        获取实际的 默认数据库连接端口

        （子类必须实现该方法）
        """
        raise self.get_error_tip()
