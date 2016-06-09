function match_passwords(field1, field2, formid) {
    function set_match_fields(field1, field2) {
        $.each([field1, field2], function (key, value) {
            $('<span class="form-control-feedback glyphicon" aria-hidden="true"></span>').appendTo($('input[name="' + value + '"]').parent());
            $('input[name="' + value + '"]').closest('.form-group').addClass('has-feedback');
        });
        $('<span class="help-block" style="color:#a94442"></span>')
            .appendTo($('input[name=' + field2 + ']').parent());
    };

    function is_match(field1, field2) {
        if ($('input[name=' + field1 + ']').val() != $('input[name=' + field2 + ']').val()) {
            return false
        } else {
            return true
        }
    };

    function offer_feedback(field1, field2) {
        if (is_match(field1, field2) == false) {
            $.each([field1, field2], function (key, value) {
                $('input[name="' + value + '"]').css({border: 'solid 1px #a94442'}).siblings('span.form-control-feedback').removeClass('text-success glyphicon-ok').addClass('text-error glyphicon-remove');
                $('.help-block').html('Passwords do not match.')
            });
        } else if (is_match(field1, field2) == true) {
            $.each([field1, field2], function (key, value) {
                $('input[name="' + value + '"]').css({border: '1px solid #ccc'}).siblings('span.form-control-feedback').addClass('text-success glyphicon-ok').removeClass('text-error glyphicon-remove');
                $('.help-block').html('');
            });
        }
    }

    function watch_fields(field1, field2) {
        $('input[name="' + field1 + '"]').bind('input propertychange', function () {
            offer_feedback(field1, field2);
        });
        $('input[name="' + field2 + '"]').bind('input propertychange', function () {
            offer_feedback(field1, field2);
        });
    };

    set_match_fields(field1, field2);
    watch_fields(field1, field2);

    $(formid).on('submit', function (e) {
        if (is_match(field1, field2) == false) {
            e.preventDefault();
            offer_feedback(field1, field2);
            $('input[name="'+field2+'"]').addClass('shake');
            setTimeout(function () {
                $(this).removeClass('shake')
            }, 2000);
        } else {
            //submit
        }
        ;
    });
};



