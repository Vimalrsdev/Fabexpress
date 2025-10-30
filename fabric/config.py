import urllib
import os



class Config(object):
    SECRET_KEY = ''
    API_KEY = ''
    JWT_SECRET_KEY = ""
    # Edited by MMM
    FCM_KEY = ''
    # Edited by MMM
    DEBUG = True
    TESTING = True
    PROPAGATE_EXCEPTIONS = True
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False


# class ProductionConfig(Config):
#     DEBUG = False
#     TESTING = False
#     db = "CustomerApp"
#     db_server_ip = "15.207.227.247"
#     db_user = os.getenv("LIVE_DB_USER")
#     db_passwd = os.getenv("LIVE_DB_PASSWD")
#     params = urllib.parse.quote_plus("DRIVER={ODBC Driver 17 for SQL Server};"
#                                      f"SERVER={db_server_ip};"
#                                      f"DATABASE={db};"
#                                      f"UID={db_user};"
#                                      f"PWD={db_passwd}")
#     SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect={}".format(params)

class ProductionConfig(Config):
    db = ""
    # db_server_ip = "3.7.90.235"
    db_server_ip = ""
    # db_server_ip = "15.207.227.247"
    # db_server_ip =  "192.168.202.11"
    db_user = os.getenv("")
    db_passwd = ""
    params = urllib.parse.quote_plus("DRIVER={ODBC Driver 17 for SQL Server};"
                                     f"SERVER={db_server_ip};"
                                     f"DATABASE={db};"
                                     f"UID={db_user};"
                                     f"PWD={db_passwd}")
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect={}".format(params)


class DevelopmentConfig(Config):
    db = ""
    # db_server_ip = "3.7.90.235"
    db_server_ip = ""
    # db_server_ip = "15.207.227.247"
    # db_server_ip = "192.168.202.11"
    db_user = os.getenv("")
    db_passwd = os.getenv("")
    params = urllib.parse.quote_plus("DRIVER={ODBC Driver 17 for SQL Server};"
                                     f"SERVER={db_server_ip};"
                                     f"DATABASE={db};"
                                     f"UID={db_user};"
                                     f"PWD={db_passwd}")
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc:///?odbc_connect={}".format(params)


