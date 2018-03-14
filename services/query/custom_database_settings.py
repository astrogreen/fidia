postgres = {'host': 'localhost',
            'port': 15300,
            'user': 'asvo',
            'passwd': 'lux9v84FT!L',
            'db': 'adc',
            'schema': 'devdc'
            }

presto = {'datatables': {'host': 'asvotest1',
                         'port': '8093',
                         'user': 'lharischandra',
                         'catalog': 'hive',
                         'schema': 'default'},
          'results': {'catalog': 'adc',
                      'schema': 'devdc'}
          }

# results_dir = '/Users/lharischandra/AAO/AAT_ASVO/Data/GAMA/CSV/' # User's webdav dir
# results_dir = '/net/aaoliw/opt/webdav/'
results_dir = '/tmp/adc/results_dir/'

# survey_csv_path = '/data/ingestion/swarps/swarps_ingestionv2.csv'
# survey_root = '/data/surveys'