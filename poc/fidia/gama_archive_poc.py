from __future__ import absolute_import, division, print_function, unicode_literals

# Python Standard Library Imports

import fidia
# from fidia.traits.references import ColumnReference
from fidia.traits import *


class GAMAArchive(fidia.ArchiveDefinition):
    archive_id = "GAMA-Main"

    archive_type = fidia.DatabaseArchive

    contents = ['24433', '221375']

    # For general testing, this should be set to True (commented out)
    # For testing of the system without database persistence, it should be False.
    # is_persisted = False

    column_definitions = fidia.ColumnDefinitionList([
        fidia.SQLColumn("SELECT `CATAID` as id, `logmstar` as data FROM StellarMasses", timestamp=1)
    ])

    trait_mappings = [
        TraitMapping(Table, 'mass', [
            TraitPropertyMapping('mass', "GAMA-Main:SQLColumn:SELECT `CATAID` as id, `logmstar` as data FROM StellarMasses:1")
        ])
    ]



if __name__ == "__main__":
    ar = GAMAArchive(database_url="mysql+mysqldb://agreen:agreen@10.80.10.137/dr2")
    print(ar['24433'].table['mass'].mass)