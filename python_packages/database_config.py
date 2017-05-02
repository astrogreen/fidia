local_default = 'postgres'  # values: sqlite, postgres
local_postgres = {'host': 'localhost',
                  'user': 'lmannering',
                  'passwd': '987dfkjshdf!p',
                  'db': 'aaodc'}

local_sqlite = {'file': 'db file path'}

postgres_svr = {'host': 'asvotest1.aao.gov.au',
                'user': 'asvo',
                'passwd': 'a1s9v8o4!P',
                'db': 'aaodc'}

try:
    from custom_database_config import *
except ImportError:
    pass
