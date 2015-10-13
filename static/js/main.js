//FORM BEHAVIOUR - - - - - - - - - - - -
//TODO populate FIELDS from backend
var Fields={                                                        //field-types 'classes' with their corresponding 'columns'
    "select":["select"],
    "join":["joinA", "joinB"],
    "filter":["filter"],
};
//for (var fieldClass in Fields){
//    $.each(Fields[fieldClass],function(i, fieldColumns){
//    });
//};
var plusButton='add-field';
var minusButton='remove-field';

function FormLogic(){
    var selector = '.select-input';
    var fieldTotalLength=$(selector).length;

    if ($(selector).filter(":hidden").size()==fieldTotalLength-1){

            $('#joinWrapper').hide();
    }
    else {
            $('#joinWrapper').show();
    }
}


function updateForm(currentFieldType, showHideIndex){               //style newly displayed <select multiple>
        $('#id_'+currentFieldType+'_columns_'+showHideIndex).multiselect({      //using multiselect
                includeSelectAllOption: true,
                disableIfEmpty: true,
                enableFiltering:true,
                maxHeight: 200,
                numberDisplayed: 20,
                nonSelectedText: 'Columns'
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

            $.each(Fields[fieldClass],function(i, fieldColumns){
                updateForm(fieldColumns, showHideIndex);                  //update the form height if new elements shown/hidden
                console.log(fieldColumns+showHideIndex);
            })
        }
    };
    FormLogic();
}

function HideThisField(){
    inputRow=$(this).parents("[id*='-input']");

    $(inputRow).hide();                       //hide parent row with matching class (e.g., join-input)

    updateHeights();                                                //update the form height accordingly

    $(inputRow).find('.chained-parent-field').each(function(){
        parent_id = $(this).attr('id');
        chained_id = $(this).attr('chained_ids');

        $('#'+parent_id).val('');                                       //reset the select
        $('#'+chained_id+' option:selected').each(function() {
                $(this).prop('selected', false);
        });
        $('#'+chained_id).val('');
        $('#'+chained_id+' option').remove();
        $('#'+chained_id).multiselect('rebuild');

    });

    $(inputRow).find('input[type=text], select').val("");
    $(inputRow).find("select option:first-child").attr("selected", "selected");
    $(inputRow).find('input:checkbox').removeAttr('checked');

    FormLogic();

}

$('.'+plusButton).on("click", ShowNewField);                        //Bind functions to click events on buttons
$('.'+minusButton).on("click", HideThisField);
//END FORM BEHAVIOUR - - - - - - - - - - -

$( document ).ready(function() {                                    //FORM INITIAL STATE
    $('[data-toggle="popover"]').popover();

    for (var fieldClass in Fields){
        $('.remove-field').parents('.'+fieldClass+'-input').hide();
        var fieldTotalLength=$('.'+fieldClass+'-input').length;

        $.each(Fields[fieldClass],function(i, fieldColumns){
            for (j=0; j<fieldTotalLength; j++){
                $('#id_'+fieldColumns+'_columns_'+j+' option:contains(--------)').remove();
                updateForm(fieldColumns,j);
            }
        });

    };
    FormLogic();

});


//TODO: join appears once two tables selected, pre-populate with table 1 and 2