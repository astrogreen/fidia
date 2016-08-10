$(".panel-group .panel-heading a")
        .each(function () {
            if ($(this).children('i').hasClass('fa-caret-down')) {
                var pointer = $(this).attr('href').toString();
                console.log(pointer);
                // If open, switch the caret to upwards-facing
                if ($(pointer).hasClass('in')) {
                    console.log('EXPANDED');
                    $(this).children('i.fa-caret-down').removeClass('fa-caret-down').addClass('fa-caret-up');
                }
            }

        })
        .click(function () {

            $(this).find('i').toggleClass('fa-caret-up fa-caret-down');
        });