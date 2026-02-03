"""
VeinLine backend package init.

This project targets MySQL. On Windows, installing `mysqlclient` often requires
native build tools. To keep local setup simple and still use MySQL, we use
PyMySQL and make it compatible with Django's MySQL backend.
"""

import pymysql

pymysql.install_as_MySQLdb()


