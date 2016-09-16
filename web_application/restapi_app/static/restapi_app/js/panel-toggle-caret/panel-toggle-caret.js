$(".panel-group .panel-heading a")
        .each(function () {
            if ($(this).children('i').hasClass('fa-caret-down')) {

                // pointer == panel
                var pointer = $($(this).attr('href').toString());
                // this = anchor
                var anchor = $(this);

                // If open, switch the caret to upwards-facing
                if (pointer.hasClass('in')) {
                    anchor.children('i.fa-caret-down').removeClass('fa-caret-down').addClass('fa-caret-up');
                }
                anchor.click(function () {
                    $(this).find('i').toggleClass('fa-caret-up fa-caret-down');
                });

                var _data = {anchor:anchor, pointer:pointer};
                pointer.on('hidden.bs.collapse', function (e) {
                    // bind data so can access anchor and pointer in this scope.
                    // when event hidden.bs.collapse is triggered:

                    if (_data.pointer.hasClass('in')) {
                        _data.anchor.children('i.fa-caret-down').removeClass('fa-caret-down').addClass('fa-caret-up');
                    } else {
                        _data.anchor.children('i.fa-caret-up').removeClass('fa-caret-up').addClass('fa-caret-down');
                    }
                }.bind(_data))
            }

        });
