

FIDIA_DIR=$PWD/../../python_packages/fidia
export DIAGRAM_DIR=$PWD/

# Create a test function which prints an error on exit 
# (see http://stackoverflow.com/questions/5195607/bash-beginner-check-exit-status)
function check {
    echo "$@"
    "$@"
    local mystatus=$?
    if [ $mystatus -ne 0 ]; then
        echo "Error with command '$1'"
        exit
    fi
}

function bluedot {
    if [[ -e classes_${1}.dot ]]; then  
        cat classes_${1}.dot | sed 's/"green"/"black"/' | dot -Tpdf >| classes_${1}.pdf
    fi
    if [[ -e packages_${1}.dot ]]; then
        cat packages_${1}.dot | sed 's/"green"/"black"/' | dot -Tpdf >| packages_${1}.pdf
    fi
}

# UML Diagram for FIDIA Trait class inehritance:

check pyreverse -o dot -p traits $FIDIA_DIR/traits --ignore=utilities.py
bluedot traits


# check pyreverse -o pdf -p trait_properties $FIDIA_DIR/traits/trait_property.py --ignore=utilities.py


# UML Diagram for whole of FIDIA:

check pyreverse -o dot -p fidia $FIDIA_DIR -fALL -mn --ignore=utilities.py,data_types.py,exceptions.py,slogging.py,dataset.py,galaxy.py,dynamo.py,data_retriver.py,aaodc_parquet_cache.py,property_collections.py,sami.py,catalog_traits.py,galaxy_traits.py,generic_traits.py,meta_data_traits.py,smart_traits.py,stellar_traits.py,example_archive.py,trait_property.py,trait_key.py,abstract_base_traits.py
bluedot fidia

check pyreverse -o pdf -p fidia_exceptions $FIDIA_DIR/exceptions.py 


# check pyreverse -o pdf -p fidia_all $FIDIA_DIR -fALL -my --ignore=utilities.py,data_types.py,exceptions.py,slogging.py,dataset.py,galaxy.py,dynamo.py,data_retriver.py,aaodc_parquet_cache.py,property_collections.py,sami.py



# UML Diagram for SAMI
check pyreverse -o dot -p sami_fidia $FIDIA_DIR/archive/sami.py -fALL -mn --ignore=utilities.py


# Plugin Diagram for SAMI

check python <<EOF
import os
from fidia import reports
from fidia.archive import sami

ar = sami.SAMIDR1PublicArchive("/Users/agreen/Documents/ASVO/test_data/sami_test_release/",
                               "dr1_catalog/dr1_20160720.txt")

output = reports.schema_hierarchy3(ar.available_traits)

with open(os.environ['DIAGRAM_DIR'] + "/sami_diagram.dot", 'w') as f:
    f.write(output)
EOF
dot -Tpdf sami_diagram.dot > sami_diagram.pdf
