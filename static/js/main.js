$('.form-group > button').addClass('pull-right');
cloneIndex=1;
function updateForm(cloneIndex){
    $('#id_testColumns'+cloneIndex).multiselect({
            includeSelectAllOption: true,
            maxHeight: 200,
            numberDisplayed: 20,
            nonSelectedText: 'Select Columns'
     });

    $("#id_testCat"+cloneIndex).on("change", function(){$('#id_testColumns'+cloneIndex).multiselect('rebuild')});
    updateHeights();
}

//CLONE FIELDS
var cloneClass='.cloned-input';
var cloneId = 'cloned-input';
var plusButton='add-field';
var minusButton='remove-field';
var containerId='#return-fields';
var cloneIndex=1;
var totalLength=$(cloneClass).length;
console.log(totalLength);

$('.remove-field').parents(cloneClass).hide();

function updateHeights(){
//    $('.form-container').height($('.form-container').parent().innerHeight());
    $('#returnWrapper').height($('#return-fields').height());
};
updateHeights();
function clone(){
    if (cloneIndex >= totalLength){
        cloneIndex=1
    }
    cloneIndex++;
    if ($('#'+cloneId + cloneIndex).is(":visible")){
        cloneIndex++;
    };
    $('#'+cloneId + cloneIndex).show();
    updateForm(cloneIndex);
    console.log(cloneIndex);
}
function remove(){
    $(this).parents(cloneClass).hide();
//    cloneIndex--;
    updateHeights();
    console.log(cloneIndex);
}

$('.'+plusButton).on("click", clone);
$('.'+minusButton).on("click", remove);
//END CLONE FIELDS

$( document ).ready(function() {

});