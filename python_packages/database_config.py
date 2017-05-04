local_default = 'postgres'  # values: sqlite, postgres
local_postgres = {'host': 'localhost',
                  'user': 'lloyd',
                  'passwd': '',
                  'db': 'aaodc'}

local_sqlite = {'file': '/Users/lharischandra/Code/asvo/web_application/db.sqlite3'}

postgres_svr = {'host': 'asvotest1',
                'user': 'user',
                'passwd': '',
                'db': 'aaodc'}


try:
    from custom_database_config import *
except ImportError:
    pass