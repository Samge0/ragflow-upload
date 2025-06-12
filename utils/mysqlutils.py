#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2022/6/4 下午6:28
# @Author  : Samge
from abc import abstractmethod
import pymysql
import logging

from utils import timeutils

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
            self.set_transaction_isolation()
        except Exception as e:
            timeutils.print_log(f'连接数据库异常: {e}')
            pass

    def query_list(self, sql: str) -> list:
        """
        有返回值的sql执行
        :param sql:
        :return: 字典列表
        """
        try:
            # 检查连接是否断开，如果断开就进行重连
            if self.conn.ping(reconnect=True):
                # 只有在真正重连后才需要重新设置事务隔离级别
                self.set_transaction_isolation()
            cur = self.cursor
            cur.execute(sql)
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, self.parse_encoding(row))) for row in cur.fetchall()]
        except Exception as e:
            timeutils.print_log(f'query_list 查询数据异常: {e}')
            return []

    def execute(self, sql: str) -> bool:
        """
        无返回的sql执行
        :param sql:
        :return: True=执行成功, False=执行失败
        """
        try:
            if self.conn.ping(reconnect=True):
                # 只有在真正重连后才需要重新设置事务隔离级别
                self.set_transaction_isolation()
            cur = self.cursor
            cur.execute(sql)
            self.conn.commit()
            return True
        except Exception as e:
            timeutils.print_log(f'execute 执行sql异常，sql = {sql}\n error: {e}')
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
            timeutils.print_log(f'close_connect 已关闭数据库连接')
        except Exception as e:
            timeutils.print_log(f'close_connect 关闭数据库异常: {e}')

    def child_close(self) -> None:
        """
        提供给子类处理的关闭操作
        """
        pass
        
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

    def set_transaction_isolation(self):
        """设置事务隔离级别为读已提交"""
        try:
            self.cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
            self.conn.commit()
        except Exception as e:
            timeutils.print_log(f'设置事务隔离级别异常: {e}')
