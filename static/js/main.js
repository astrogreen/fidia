//FORM BEHAVIOUR - - - - - - - - - - - -
//TODO: ADD IN FILTER FIELDS, allow passing of field type (filter, return etc) as class/id

parent='';
chained=$(this).attr('chained_ids');

function updateForm(cloneIndex){                    //style newly displayed <select multiple>
    $('#id_columns_'+cloneIndex+' option:contains(--------)').remove();

    $('#id_columns_'+cloneIndex).multiselect({      //using multiselect
            includeSelectAllOption: true,
            disableIfEmpty: true,
            maxHeight: 200,
            numberDisplayed: 20,
            nonSelectedText: 'Select Columns'
     });                                            //rebuild the multiselect to reflect new data when the parent
    updateHeights();                                //update container height to reflect new styling
}

//CLONE [HIDE/SHOW FIELDS]
//TODO: RENAME VARIABLE NAMES WITH SOMETHING MORE RELEVANT - CLONE ISN'T THE BEHAVIOUR OF THE FUNCTION ANYMORE
var cloneClass='.return-input';                     //set common class for show/hide behaviour to target
var cloneId = 'return-input';
var plusButton='add-field';
var minusButton='remove-field';
var cloneIndex=0;                                   //Reset the index (used to track the number of hidden/displayed fields)
var totalLength=$(cloneClass).length;               //totalLength == number of total available elements
$('.remove-field').parents(cloneClass).hide();      //Hide all fields but this one

//ALTER THE FORM HEIGHT BASED ON THE NUMBER OF FIELDS CURRENTLY SHOWN
function updateHeights(){
    $('#returnWrapper').height($('#return-fields').height());
};

function ShowNewField(){
    if (cloneIndex >= totalLength -1){
        $('#maxFieldsModal').modal('show');
        cloneIndex=0                                //Reset the index if user has clicked the 'plus' button
    }                                               //more than the allowable number of fields.
    cloneIndex++;
    while ($('#'+cloneId + cloneIndex).is(":visible")){
        cloneIndex++;
    }
    $('#'+cloneId + cloneIndex).show();
    updateForm(cloneIndex);                         //update the form to reflect the multiselects and new height
}
function HideThisField(){                           //Hide the parent div with the cloneClass containing $this
    $(this).parents(cloneClass).hide();             //button
    updateHeights();                                //update the form height accordingly

    parent_id=$(this).parents(cloneClass).find('.chained-parent-field').attr('id');
    chained_id=$(this).parents(cloneClass).find('.chained-parent-field').attr('chained_ids');

    $('#'+parent_id).val('');
    $('#'+chained_id+' option:selected').each(function() {
            $(this).prop('selected', false);
    });
    $('#'+chained_id).multiselect('refresh');

    cloneIndex=0;                                   //iterate up the list again
}

$('.'+plusButton).on("click", ShowNewField);        //Bind functions to click events on buttons
$('.'+minusButton).on("click", HideThisField);
//END FORM BEHAVIOUR - - - - - - - - - - -

$( document ).ready(function() {
    updateForm(cloneIndex);
});