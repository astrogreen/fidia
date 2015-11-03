from astrospark import mediator

CAT = ()

COLUMNS = {}

tblnames = mediator.get_tables()

for table in tblnames:
    tableName = table.name
    CAT += ((tableName, tableName),)
    COLUMNS.update({tableName: mediator.get_column_names(tableName)})


