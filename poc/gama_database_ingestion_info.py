import sys
import subprocess

from collections import OrderedDict

import sqlalchemy as sa

cataid_table_list = [
    "InputCatA",
    "GalexMain",
    "GalexObsInfo",
    "GalexSimpleMatch",
    "GalexAdvancedMatch",
    "GalexCoGPhot",
    "TilingCat",
    "ApMatchedCat",
    "EmLinesPhys",
    "SersicCatAll",
    "kcorr_z00",
    "kcorr_z01",
    "EnvironmentMeasures",
    "StellarMasses",
    "G3CGal",
    "DistancesFrames",
    "SpStandards",
    "SpecObj"
]

specall_table_list = [
    "AATSpecAll",
    "AATSpecAllzAll",
    "ExternalSpecAll",
    "SpecLines",
    "EmLinesPhysGAMA",
    "EmLinesPhysSDSS",
    "ExternalzAll",
    "LTSpecAll",
    "AATRunzResults",
]

def execute_query(query, colnames=True):
    command = ["mysql", "-h10.80.10.137", "-pagreen", "-uagreen", "-B"]
    if not colnames:
        command.append("-N")
    # Add Database name
    command.append("dr2")
    # Query
    command.extend(["-e", "{query}".format(query=query)])
    output = subprocess.check_output(command)
    return output.decode("utf-8")

def print_rows(data):
    columns = list(list(data.values())[1].keys())

    format_string = "{:>20s}" + " ".join(["{:>10s}" for i in columns])

    print(
        format_string.format("Table", *columns)
    )

    for table in data:
        cells = [table]
        cells.extend(
                    [data[table][c] for c in columns])
        print(
            format_string.format(*cells)
        )


output = OrderedDict()
for table in cataid_table_list:
    output[table] = OrderedDict()
    distinct_query = "SELECT count(DISTINCT CATAID) FROM {table};".format(table=table)
    full_query = "SELECT count(CATAID) FROM {table};".format(table=table)
    output[table]['distinct'] = execute_query(distinct_query, colnames=False).strip()
    output[table]['full'] = execute_query(full_query, colnames=False).strip()

print("CataID tables")
print_rows(output)

spec_out = OrderedDict()
for table in specall_table_list:
    spec_out[table] = OrderedDict()
    distinct_query = "SELECT count(DISTINCT SPECID) FROM {table};".format(table=table)
    full_query = "SELECT count(SPECID) FROM {table};".format(table=table)
    spec_out[table]['distinct'] = execute_query(distinct_query, colnames=False).strip()
    spec_out[table]['full'] = execute_query(full_query, colnames=False).strip()
    try:
        spec_out[table]['cataid'] = execute_query(
            "SELECT count(CATAID) FROM {table}".format(table=table),
            colnames=False
        ).strip()
    except:
        print("Table %s has no cataid" % table)
        spec_out[table]['cataid'] = ""

print("SpecID tables")
print_rows(spec_out)

# engine = sa.create_engine('mysql://agreen:agreen@10.80.10.137/dr2', echo=True)

# metadata = sa.MetaData(engine)