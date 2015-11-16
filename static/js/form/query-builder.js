////FORM BEHAVIOUR - - - - - - - - - - - -
var Fields={                                                        //field-types 'classes' with their corresponding 'columns'
    "select":["select"],
    "join":["joinA", "joinB"],
    "filter":["filter"],
};
////for (var fieldClass in Fields){
////    $.each(Fields[fieldClass],function(i, fieldColumns){
////    });
////};
var plusButton='add-field';
var minusButton='remove-field';
var selector = '.select-input';

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

            if (showHideIndex >= fieldTotalLength ){
                $('#maxFieldsModal').modal('show');                 //SHOW MODAL IF GREATER THAN ALLOWABLE NUMBER
            } else {
                var rowID='#'+fieldTypeSelector + showHideIndex;
                ShowInputFields(rowID);                             //SHOW THIS NEXT AVAILABLE ROW, TURN ON VALIDATION OF INPUTS
            };
        };
    };
    FormLogic();
};

function EnableDisableValidation(fieldName, enableBool){
    var message = null;
    //IF THE INPUT ELEMENT HAS VALIDATION REQUIREMENTS SET (WHETHER ENABLED OR NOT)
    if ((fieldName)&&(($('#queryForm').data('formValidation').getOptions(fieldName))!== null)){

if (enableBool==false && fieldName== 'select-input0'){console.log(enableBool);}

        if ((fieldName=='select_cat_0' && enableBool==false) || (fieldName=='select_columns_0' && enableBool == false)){
            message = 'cannot change select-input0';
        } else {
            // CHANGE VALIDATION (NOT ON FIRST SELECT ROW)
            $('#queryForm').formValidation('enableFieldValidators', fieldName, enableBool);
            message= 'state validated';
            $('#queryForm').formValidation('revalidateField', fieldName);
//            console.log(fieldName+' '+enableBool);
        }
   };
   return message;
}

function ShowInputFields(parentID){
    $(parentID).show();                                    //SHOW THIS NEXT AVAILABLE ROW (VALIDATION ONLY ON VISIBLE ELEMENTS)
    $(parentID).find('input, select')
        .not(':input[type=button], :input[type=submit], :input[type=reset]')
        .each(function(){
            var elNAME=this.name;
            var elID='#'+this.id;
            if (elNAME){
//                console.log('TURNING ON: '+rowID+' with NAME: '+elNAME);
                EnableDisableValidation(elNAME, true);
                //IF ELEMENT HAS MULTISELECT ENABLED
                if ($(this).siblings('.btn-group').children('button.multiselect').length != 0){
                    $(elID).multiselect('rebuild');
                }
                //TURNING THIS ON VALIDATES ON SHOW - user can see what they've missed
                $('#queryForm').formValidation('revalidateField', elNAME);
            };
        });
};

function ClearInputFields(parentID) {

    $(parentID).find('input, select')
               .not(':input[type=button], :input[type=submit], :input[type=reset]')
               .each(function(){
                   var elNAME=this.name;
                   //TURN OFF VALIDATION (MUST BE BEFORE REBUILD MULTISELECT)
                   EnableDisableValidation(elNAME, false);
                   //REBUILD MULTISELECTS
                    switch(this.type) {
                        case 'text':
                            $(this).val('');
                            break;
                        case 'textarea':
                            break;
                        case 'file':
                            break;
                        case 'select-one':              //FOR BOTH CASES
                        case 'select-multiple':
//                            $(this).val(''); //use prop selected false instead cross-browser
                            $(this).find(" option:selected").prop("selected", false);
//                            console.log($(this).attr('ID'));
                            //RESET MULTISELECTS
                            if ($(this).siblings('.btn-group').children('button.multiselect').length != 0){
                                //IF A CHAINED-ELEMENT REMOVE ALL OPTIONS
                                if ($(this).attr('ajax_url')){
//                                    console.log('chained ELEMENT');
                                    $('#'+this.id+' option').remove()
                                }
                                //IF PARENT OR NOT CHAINED JUST REBUILD
                                $(this).multiselect('rebuild');
//                                console.log('MULTISELECT REBUILD');
                            }
                            break;
                        case 'checkbox':
                            this.checked = false;
                            break;
                        case 'radio':
                            this.checked = false;
                            break;
                    }
               });
};

function HideThisField(){
    var row=$(this).parents("[id*='-input']");
    $(row).hide();                                                  //HIDE THE PARENT ROW OF THE BUTTON
    var rowID='#'+row.attr('id');
    ClearInputFields(rowID);
    FormLogic();
};

function FormLogic(){
    //LINK JOINS TO SELECTS
    var fieldTotalLength=$(selector).length;
    var hideCounter=0;
    for (var t=1; t < fieldTotalLength;t++){
        var p=t-1;
        if ($('#select-input'+t).css('display') == 'inline-block'){
            ShowInputFields('#join-input'+p);
            $('#joinWrapper').show();
        } else if ($('#select-input'+t).css('display') == 'none') {
            $('#join-input'+p).hide();
            ClearInputFields('#join-input'+p);
            hideCounter++;
            if (hideCounter==fieldTotalLength-1){$('#joinWrapper').hide();}
        };
    };

    //ALTER AVAILABLE OPTIONS TO FILTER AND JOIN FIELDS
    //CREATE A LIST OF AVAILABLE OPTIONS (OCCURS AFTER SetUpForm())
    var selectOptions = {};
    $.each($('.select-input'),function(index){
        var selectId=$(this).find(' select.chained-parent-field').attr('id');
        selectOptions[$("#"+selectId+" option:selected").text()]=$("#"+selectId+" option:selected").val();
    });

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
                            } else {
                            //OPTION ISN'T IN JOIN/FILTER CATALOGUE OPTIONS :- ADD
                                $el.append($("<option></option>")
                                .attr("value", value).text(key));
                                //IF MULTISELECT EXISTS
                                if ($el.siblings('.btn-group').children('button.multiselect').length != 0){
                                    $el.multiselect('rebuild');
                                    var elNAME = $el.attr('name');
//                                    $('#queryForm').formValidation('revalidateField', elNAME);
                                };
                            };
                        });
                        // now cycle through the select options and remove all not in select options array
                        $el.find(" option").each(function() {
                            if (selectOptions[this.text] ){

                            } else {
                                if (this.text!='catalogue'){
                                    //find selects with this value selected
                                    //and rebuild those chained children multiselects
                                    if ($el.find(' option:selected').val()==this.value){
                                        var chained_id = $el.attr('chained_ids');
//                                        console.log('UPDATE '+chained_id);
                                        $('#'+chained_id).val('');
                                        $('#'+chained_id+' option').remove();
                                    }
                                    //then loop over all parent selects and remove option
                                    $el.find('option[value="'+this.value+'"]').remove();
                                    if ($el.siblings('.btn-group').children('button.multiselect').length != 0){
                                        $el.multiselect('rebuild');
                                        var elNAME = $el.attr('name');
//                                        $('#queryForm').formValidation('revalidateField', elNAME);
                                    }
                                }
                            };
                        });
                    };
                });
            });
        }
    };
};

////FORMVALIDATION CUSTOM VALIDATORS
function SetUpForm(){
    //HIDE ALL BEYOND 0
    for (var fieldClass in Fields){
        $('.remove-field').parents('.'+fieldClass+'-input').hide();
        var fieldTotalLength=$('.'+fieldClass+'-input').length;
        //REMOVE SOME DEFAULT DJANGO OPTIONS AND EMPTY THE FILTER AND JOIN CATS
        $.each(Fields[fieldClass],function(i, fieldColumns){
            for (var j=0; j<fieldTotalLength; j++){
                $('#id_'+fieldColumns+'_columns_'+j+' option:contains(--------)').remove();
            }
            if (fieldClass != 'select'){
                $('[id^=id_'+fieldColumns+'_cat_]').each(function() {
                        var $el=$(this);
                        $el.empty();
                        $el.append($("<option></option>")
                                        .attr("value", '').text('catalogue'));
                        $el.prop('disabled', 'disabled');
                });
            };
        });
    };

    //ADD SPECIFIC VALIDATORS
    $('#queryForm')
        .formValidation({
            framework: 'bootstrap',
            // Exclude only disabled fields
            // The invisible fields set by Bootstrap Multiselect must be validated
            excluded: ':disabled',
            icon: {
                valid: 'glyphicon glyphicon-ok',
                invalid: 'glyphicon glyphicon-remove',
                validating: 'glyphicon glyphicon-refresh'
            },
            fields: {
                select_cat_0: {
                    enabled:true,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        }
                    }
                },
                select_cat_1: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        }
                    }
                },
                select_cat_2: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        }
                    }
                },
                select_cat_3: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        }
                    }
                },
                select_cat_4: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        }
                    }
                },
                select_columns_0: {
                    enabled:true,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                select_columns_1: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                select_columns_2: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                select_columns_3: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                select_columns_4: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                // JOINS
                joinA_cat_0: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        }
                    }
                },
                joinA_cat_1: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        }
                    }
                },
                joinA_cat_2: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        }
                    }
                },
                joinA_cat_3: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        }
                    }
                },
                joinA_columns_0: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                joinA_columns_1: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                joinA_columns_2: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                joinA_columns_3: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                //
                joinB_cat_0: {
                    enabled: false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        },
                        callback: {
                            message: 'Join catalogues must be unique',
                            callback: function(value, validator, $field) {
                                //IF JOINA == JOINB ERROR
                                if ($('#id_joinA_cat_0').find(' option:selected').val()==$('#id_joinB_cat_0').find(' option:selected').val()) {var dummy = 0;} else {var dummy=1;}
                                return (dummy != null && dummy >0);
                            }
                        }
                    }
                },
                joinB_cat_1: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        },
                        callback: {
                            message: 'Join catalogues must be unique',
                            callback: function(value, validator, $field) {
                                //IF JOINA == JOINB ERROR
                                if ($('#id_joinA_cat_1').find(' option:selected').val()==$('#id_joinB_cat_1').find(' option:selected').val()) {var dummy = 0;} else {var dummy=1;}
                                return (dummy != null && dummy >0);
                            }
                        }
                    }
                },
                joinB_cat_2: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        },
                        callback: {
                            message: 'Join catalogues must be unique',
                            callback: function(value, validator, $field) {
                                //IF JOINA == JOINB ERROR
                                if ($('#id_joinA_cat_2').find(' option:selected').val()==$('#id_joinB_cat_2').find(' option:selected').val()) {var dummy = 0;} else {var dummy=1;}
                                return (dummy != null && dummy >0);
                            }
                        }
                    }
                },
                joinB_cat_3: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        },
                        callback: {
                            message: 'Join catalogues must be unique',
                            callback: function(value, validator, $field) {
                                //IF JOINA == JOINB ERROR
                                if ($('#id_joinA_cat_3').find(' option:selected').val()==$('#id_joinB_cat_3').find(' option:selected').val()) {var dummy = 0;} else {var dummy=1;}
                                return (dummy != null && dummy >0);
                            }
                        }
                    }
                },
                joinB_columns_0: {
                    enabled: false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                joinB_columns_1: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                joinB_columns_2: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                joinB_columns_3: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                // FILTERS
                filter_cat_0: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        }
                    }
                },
                filter_cat_1: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        }
                    }
                },
                filter_cat_2: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        }
                    }
                },
                filter_cat_3: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        }
                    }
                },
                filter_cat_4: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select a catalogue'
                        }
                    }
                },
                filter_columns_0: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                filter_columns_1: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                filter_columns_2: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                filter_columns_3: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                filter_columns_4: {
                    enabled:false,
                    validators: {
                        notEmpty: {
                            message: 'Select columns'
                        }
                    }
                },
                //TODO add additional SQL validation
                filter_value_0: {
                    enabled:false,
                    validators: {
                        notEmpty:{
                            message:'Please provide a value'
                        },
                        regexp: {
                            regexp: /^[a-zA-Z0-9-_.,]+$/i,
                            message: 'Value can consist of alphanumeric characters, underscores and hyphens only'
                        }
                    }
                },
                filter_value_1: {
                    enabled:false,
                    validators: {
                        notEmpty:{
                            message:'Please provide a value'
                        },
                        regexp: {
                            regexp: /^[a-zA-Z0-9-_.,]+$/i,
                            message: 'Value can consist of alphanumeric characters, underscores and hyphens only'
                        }
                    }
                },
                filter_value_2: {
                    enabled:false,
                    validators: {
                        notEmpty:{
                            message:'Please provide a value'
                        },
                        regexp: {
                            regexp: /^[a-zA-Z0-9-_.,]+$/i,
                            message: 'Value can consist of alphanumeric characters, underscores and hyphens only'
                        }
                    }
                },
                filter_value_3: {
                    enabled:false,
                    validators: {
                        notEmpty:{
                            message:'Please provide a value'
                        },
                        regexp: {
                            regexp: /^[a-zA-Z0-9-_.,]+$/i,
                            message: 'Value can consist of alphanumeric characters, underscores and hyphens only'
                        }
                    }
                },
                filter_value_4: {
                    enabled:false,
                    validators: {
                        notEmpty:{
                            message:'Please provide a value'
                        },
                        regexp: {
                            regexp: /^[a-zA-Z0-9-_.,]+$/i,
                            message: 'Value can consist of alphanumeric characters, underscores and hyphens only'
                        }
                    }
                },
            }
        });
    //BUILD MULTISELECTS
    //ON CATALOGUES
    $('#queryForm').find('[name^="select_cat_"],[name^="joinA_cat_"],[name^="joinB_cat_"],[name^="filter_cat_"]')
    .each(function(index){
        ID=$(this).attr('ID');
        var elNAME=$(this).attr('name');
        $('#'+ID).multiselect({
            includeSelectAllOption: true,
            enableCaseInsensitiveFiltering: true,
            disableIfEmpty: true,
            enableFiltering:true,
            maxHeight: 260,
            numberDisplayed: 20,
            nonSelectedText: 'catalogue',
            //ON CHANGE REVALIDATE THE FIELD
            onChange: function(element, checked) {
                $('#queryForm').formValidation('revalidateField', elNAME);
            }
        })
    });
    //ON COLUMNS
    $('#queryForm').find('[name^="select_columns_"],[name^="joinA_columns_"],[name^="joinB_columns_"],[name^="filter_columns_"]')
    .each(function(index){
        ID=$(this).attr('ID');
        var elNAME=$(this).attr('name');
        $('#'+ID).multiselect({
            includeSelectAllOption: true,
            enableCaseInsensitiveFiltering: true,
            disableIfEmpty: true,
            enableFiltering:true,
            maxHeight: 260,
            numberDisplayed: 20,
            nonSelectedText: 'columns',
            //ON CHANGE REVALIDATE THE FIELD
            onChange: function(element, checked) {
                $('#queryForm').formValidation('revalidateField', elNAME);
            }
        })
    });

    $( "#filterWrapper" ).hide();
    FilterToggle();

};
SetUpForm();


function CheckFieldState(fieldName){
    for (var fieldClass in Fields){
    $.each(Fields[fieldClass],function(i, fieldColumns){
        $('[id^=id_'+fieldColumns+'_cat_],[id^=id_'+fieldColumns+'_columns_],[id^=id_'+fieldColumns+'_value_]')
            .each(function() {
                var $el=$(this);
                var elNAME=$el.attr('NAME');
                var elID='#'+$el.attr('ID');
//                console.log(elNAME);
                row=$(this).parents("[class*='-input']");                       //find the class of the group (select, filter, join)
                rowID='#'+row.attr('ID');
                if ($(rowID).is(":visible")){                                   //IF ROW IS VISIBLE, ALLOW VALIDATION ON FIELDS
                     EnableDisableValidation(elNAME, true);
//                     console.log(rowID);
//                     $('#queryForm').formValidation('revalidateField', elNAME);
                } else {
                    EnableDisableValidation(elNAME, false);                     //ELSE DISABLE VALIDATION
                }
            });
        });
    };
}

function FilterToggle(){
    if ($("#filterWrapper").is( ":visible" )){
        $("#filterToggle").html('remove filter').removeClass('btn-info').addClass('btn-warning');
        ShowInputFields('#filter-input0');
    } else {
        $("#filterToggle").html('add filter').removeClass('btn-warning').addClass('btn-info');
        $('#queryForm').find('[id^="filter-input"]')
            .each(function(index){
                var rowID='#'+$(this).attr('ID');
                ClearInputFields(rowID);
                if (rowID != '#filter-input0'){
                    $(rowID).hide();
                }
            });
    }
};

$( document ).ready(function() {
    $('[data-toggle="popover"]').popover();
    FormLogic();
    CheckFieldState();

    $(selector+' select.chained-parent-field').change(function(){FormLogic();});

    //BIND ADD AND REMOVE BUTTONS;
    $('.'+plusButton).on("click", ShowNewField);
    $('.'+minusButton).on("click", HideThisField);

    //TOGGLE FILTER WRAPPER
    $("#filterToggle").click(function() {
        $( "#filterWrapper" ).toggle("slow", function() {
            FilterToggle();
        });
    });

    //RESET FORM BUTTON
    $('#queryReset').click(function(){
        $('#queryForm').data('formValidation').resetForm();
        SetUpForm();
        //trash and rebuild select 0
        ClearInputFields('#select-input0');
        ShowInputFields('#select-input0');

        CheckFieldState();
        FormLogic();
        $( "#filterWrapper" ).hide();
        FilterToggle();
    });
    //ON SUBMIT CHANGE BUTTON
    $('#queryForm')
        .on('success.form.fv', function(e) {
//        console.log('successful submit');
            $('#querySubmit').addClass('btn-warning')
            .html('Fetching data... <i class="fa fa-refresh fa-spin"></i>');
        });
});
