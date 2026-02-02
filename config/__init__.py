from decouple import config

if config('DB_USE_MYSQL', default=False, cast=bool):
    import pymysql
    pymysql.install_as_MySQLdb()



