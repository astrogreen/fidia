from astrospark import mediator

CAT = ()

COLUMNS = {}

tblnames = mediator.get_tables()

for table in tblnames:
    if not table == 'tilingcat': # There's problem with this table in hadoop
        CAT += ((table, table),)
        COLUMNS.update({table: mediator.get_column_names(table)})
