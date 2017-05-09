# local_default = 'postgres'  # values: sqlite, postgres
# local_postgres = {'host': 'localhost',
#                   'user': 'lloyd',
#                   'passwd': 'gemba',
#                   'db': 'aaodc'}
#
# local_sqlite = {'file': '/Users/lharischandra/Code/asvo/web_application/db.sqlite3'}
#
# postgres_svr = {'host': 'asvotest1',
#                 'user': 'user',
#                 'passwd': '',
#                 'db': 'aaodc'}

django_db = 'postgres' # values: sqlite, postgres

postgres = {'host': 'myhost',
            'user': 'myuser',
            'passwd': 'mypassword',
            'db': 'mydb'
            }

sqlite = {'file': 'path to sqlite db file'}

mappings_db = {'host': 'myhost',
               'user': 'myuser',
               'passwd': 'mypassword',
               'db': 'mydb'
               }

presto = {'megatables': {'catalog': 'cat_name',
                         'schema': 'sch_name'},
          'results': {'catalog': 'cat_name',
                      'schema': 'sch_name'}
          }

results_dir = '/path to the directory that holds results files in csv, etc./'

try:
    from custom_database_config import *
except ImportError:
    pass
