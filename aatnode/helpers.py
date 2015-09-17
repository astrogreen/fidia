from astrospark import mediator

CAT_G3CGALSINPAIR = 'G3CGalsInPair'
CAT_STELLARMASSES = 'StellarMasses'
CAT = (
    (CAT_G3CGALSINPAIR, 'G3CGalsInPair'),
    (CAT_STELLARMASSES, 'StellarMasses')
)

COLUMNS = {
    CAT_G3CGALSINPAIR: mediator.get_column_names(CAT_G3CGALSINPAIR),
    CAT_STELLARMASSES: mediator.get_column_names(CAT_STELLARMASSES)
}

