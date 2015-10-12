//FORM BEHAVIOUR - - - - - - - - - - - -
//TODO populate FIELDS from backend
var Fields={                                                        //field-types 'classes' with their corresponding 'columns'
    "select":["select"],
    "join":["joinA", "joinB"],
    "filter":["filter"],
};
var plusButton='add-field';
var minusButton='remove-field';

for (var fieldClass in Fields){
//    console.log(fieldClass);
    $.each(Fields[fieldClass],function(i, fieldColumns){
//        console.log(fieldColumns);
    });
};

function updateForm(currentFieldType, showHideIndex){               //style newly displayed <select multiple>
        $('#id_'+currentFieldType+'_columns_'+showHideIndex).multiselect({      //using multiselect
                includeSelectAllOption: true,
                disableIfEmpty: true,
                maxHeight: 200,
                numberDisplayed: 20,
                nonSelectedText: 'None'
        });
                                                                    //rebuild the multiselect to reflect new data
    updateHeights();                                                //update container height to reflect new styling
}

function updateHeights(){                                           //ALTER THE FORM HEIGHT BASED ON SHOWN FIELDS
    $('#returnWrapper').height($('#select-fields').height()+$('#join-fields').height()+$('#filter-fields').height());
};

function ShowNewField(){
    row=$(this).parents("[class*='-input']");                       //find the class of the group (select, filter, join?)
    for (var fieldClass in Fields){                                 //match it to the expected fields
        if ($(row).hasClass(fieldClass+'-input')){                  //fieldTypeSelector == join-select (common class)
            var fieldTypeSelector=fieldClass+'-input';              //specific ID is appended with a number
            var fieldTotalLength=$('.'+fieldTypeSelector).length;

            var showHideIndex=0;
            while ($('#'+fieldTypeSelector + showHideIndex).is(":visible")){
                showHideIndex++;
            }
            $('#'+fieldTypeSelector + showHideIndex).show();        //show row with ID = fieldTypeSelector+number
            if (showHideIndex >= fieldTotalLength ){
                $('#maxFieldsModal').modal('show');                 //show the modal if greater than allowed number
            }
            updateForm(fieldClass, showHideIndex);                  //update the form height if new elements shown/hidden
        }
    };

}

function HideThisField(){
    $(this).parents("[id*='-input']").hide();                       //hide parent row with matching class (e.g., join-input)
    updateHeights();                                                //update the form height accordingly

    parent_id=$(this).parents("[id*='-input']").find('.chained-parent-field').attr('id');
    chained_id=$(this).parents("[id*='-input']").find('.chained-parent-field').attr('chained_ids');


    $('#'+parent_id).val('');                                       //reset the select
    $('#'+chained_id+' option:selected').each(function() {
            $(this).prop('selected', false);
    });
    $('#'+chained_id).multiselect('refresh');
}

$('.'+plusButton).on("click", ShowNewField);                        //Bind functions to click events on buttons
$('.'+minusButton).on("click", HideThisField);
//END FORM BEHAVIOUR - - - - - - - - - - -

$( document ).ready(function() {                                    //FORM INITIAL STATE

    for (var fieldClass in Fields){
        $('.remove-field').parents('.'+fieldClass+'-input').hide();
        console.log('.'+fieldClass+'-input');
        var fieldTotalLength=$('.'+fieldClass+'-input').length;

        $.each(Fields[fieldClass],function(i, fieldColumns){
            for (j=0; j<fieldTotalLength; j++){
                $('#id_'+fieldColumns+'_columns_'+j+' option:contains(--------)').remove();
                updateForm(fieldColumns,0);
            }
        });

    };

});


//TODO: join appears once two tables selected, pre-populate with table 1 and 2