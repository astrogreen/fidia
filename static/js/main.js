//FORM BEHAVIOUR - - - - - - - - - - - -
//TODO populate FIELDS from backend
//TODO validate field input on submit for multiselect-ed dropdowns
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
var selector = '.select-input';
$('.'+plusButton).on("click", ShowNewField);                        //Bind functions to click events on buttons
$('.'+minusButton).on("click", HideThisField);

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
                updateForm(fieldColumns, showHideIndex);            //update the form height if new elements shown/hidden
            })
        }
    };
    FormLogic();
};


function HideThisField(){
    var row=$(this).parents("[id*='-input']");
    $(row).hide();                       //hide parent row with matching class (e.g., join-input)
    updateHeights();                                                //update the form height accordingly

    if ($(row).hasClass('select-input')){
        catalogueToHide=$(row).find('.chained-parent-field option:selected').text();
    } else {catalogueToHide='';}

    $(row).find('.chained-parent-field').each(function(){
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

    $(row).find('input[type=text], select').val("");
    $(row).find("select option:first-child").attr("selected", "selected");
    $(row).find('input:checkbox').removeAttr('checked');


    FormLogic(catalogueToHide);
}

function updateForm(currentField, index){               //style newly displayed <select multiple>
    var elementName='#id_'+currentField+'_columns_'+index;
    if (typeof index === 'undefined') {                 //if index is undefined, use string as ID
        var elementName = '#'+currentField;
    }
//    console.log('MULTISELECT '+elementName);
        $(elementName).multiselect({      //using multiselect
                includeSelectAllOption: true,
                disableIfEmpty: true,
                enableFiltering:true,
                maxHeight: 200,
                numberDisplayed: 20,
                nonSelectedText: 'Select columns'
        });                                                         //rebuild the multiselect to reflect new data
    updateHeights();                                                //update container height to reflect new styling
}

function updateHeights(){                                           //ALTER THE FORM HEIGHT BASED ON SHOWN FIELDS
    $('#returnWrapper').height($('#select-fields').height()+$('#join-fields').height()+$('#filter-fields').height());
};

function FormLogic(){
    var selectOptions = {};                                                    //create list of current select options (occurs after the reset if remove)
    $.each($('.select-input'),function(index){
        var selectId=$(this).find(' select.chained-parent-field').attr('id');
//        defaultOption = $(this).find(' select.chained-parent-field option:selected').first().text();
        selectOptions[$("#"+selectId+" option:selected").text()]=$("#"+selectId+" option:selected").val();
    });

    var fieldTotalLength=$(selector).length;
    if ($(selector).filter(":hidden").size()==fieldTotalLength-1){
            $('#joinWrapper').hide();
    }
    else {
            $('#joinWrapper').show();
    };

    for (var fieldClass in Fields){
        if (fieldClass != 'select'){
           $.each(Fields[fieldClass],function(i, fieldColumns){
                $('[id^=id_'+fieldColumns+'_cat_]').each(function() {
                    var $el=$(this);

                    if ($.isEmptyObject(selectOptions)){
                        $el.prop('disabled', 'disabled');
                    } else {
                        $el.prop('disabled', false);
                        $.each(selectOptions,function(key,value){
                            if ( $el.find('option[value="'+value+'"]').length>0 ){

                            } else {                                                    //option not already in list, add
                                $el.append($("<option></option>")
                                .attr("value", value).text(key));
//                                $el.multiselect('rebuild');
                            };
                        });
                        // now cycle through the select options and remove all not in select options array
                        $el.find(" option").each(function() {
                            if (selectOptions[this.text] ){

                            } else {
                                if (this.text!='Catalogue'){
                                    //find selects with this value selected
                                    //and rebuild those chained children multiselects
                                    if ($el.find(' option:selected').val()==this.value){
                                        chained_id = $el.attr('chained_ids');
                                        console.log('UPDATE '+chained_id);
                                        $('#'+chained_id).val('');
                                        $('#'+chained_id+' option').remove();
                                    }
                                    //then loop over all parent selects and remove option
                                    $el.find('option[value="'+this.value+'"]').remove();
                                    $('#'+chained_id).multiselect('rebuild');
                                }

                            };
                        });
                    };

//TODO ADD FEEDBACK
//                    $el.addClass('alert-border').delay(400).queue(function(){
//                        $(this).removeClass("alert-border");
//                        $(this).dequeue();
//                    });;

                });
            });
        } else {

        };
    };
};

//END FORM BEHAVIOUR - - - - - - - - - - -

$( document ).ready(function() {                                    //FORM INITIAL STATE
    $('[data-toggle="popover"]').popover();

    for (var fieldClass in Fields){
        $('.remove-field').parents('.'+fieldClass+'-input').hide();

        var fieldTotalLength=$('.'+fieldClass+'-input').length;
        $.each(Fields[fieldClass],function(i, fieldColumns){
            for (var j=0; j<fieldTotalLength; j++){
                $('#id_'+fieldColumns+'_columns_'+j+' option:contains(--------)').remove();
                updateForm(fieldColumns,j);
            }
            if (fieldClass != 'select'){
                $('[id^=id_'+fieldColumns+'_cat_]').each(function() {
                        var $el=$(this);
                        $el.empty();
                        $el.append($("<option></option>")
                                        .attr("value", '').text('Catalogue'));
                        $el.prop('disabled', 'disabled');
                });

            };
        });

    };

    FormLogic();
    $(selector+' select.chained-parent-field').change(function(){FormLogic();});

//STYLING
//    $("#queryForm select").each(function() {
//        if ($(this).hasClass('chained-parent-field')){
//            $(this).multiselect({
//                includeSelectAllOption: true,
//                enableFiltering: true,
//                disableIfEmpty: true,
//                maxHeight: 200,
//                numberDisplayed: 20,
////                buttonWidth: '180px',
//            });
//        } else {
//            $(this).multiselect({
//                disableIfEmpty: true,
//                maxHeight: 200,
//                numberDisplayed: 20,
//            });
//        }
//    });

    //JQUERY VALIDATION
//TODO test plugin - cost??!

//DOCS
$('body').scrollspy({
    target: '.docs-sidebar',
    offset: 40
});


});

