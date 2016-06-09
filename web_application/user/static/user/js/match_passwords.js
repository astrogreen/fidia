function match_passwords(passwordfield1, passwordfield2) {
    console.log('match-passwords');
    console.log(passwordfield1, passwordfield2);
    if ($('input[name='+passwordfield1+']').val() != $('input[name='+passwordfield2+']').val()) {
        $('input[name='+passwordfield1+']', 'input[name='+passwordfield2+']').css({border:'solid 1px #a94442'});
        $('<span class="help-block" style="color:#a94442">Passwords do not match.</span>')
            .appendTo($('input[name='+passwordfield2+']').parent());
        return false;
    } else {
        $('input[name='+passwordfield1+']', 'input[name='+passwordfield2+']').css({border: '0px'});
        $('<span class="help-block" style="color:#5aa8d8"><i class="fa fa-check"></i></span>')
            .appendTo($('input[name='+passwordfield2+']').parent());
    }
    return true;
}