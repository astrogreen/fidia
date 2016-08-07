// $(document).ready(function () {
//
//     var showchar = 100; // 50 chars shown by default
//     var ellipsestext = "...";
//     var moretext = "Read more <i class='fa fa-caret-down'></i>";
//     var lesstext = "Read less <i class='fa fa-caret-up'></i>";
//
//
//     $('.readmore').each(function () {
//         // On page load, split the content into shown and hidden elements
//         var content = $(this).html();
//
//         if (content.length > showchar) {
//
//             var c = content.substr(0, showchar);
//             var h = content.substr(showchar, content.length - showchar);
//
//             var html = '<span>' + c + '</span>' + '<span class="readmoreellipses">' + ellipsestext + '&nbsp;</span><span class="readmorecontent"><span>'
//                 + h + '</span>&nbsp;&nbsp;<a href="" class="readmorelink">' + moretext + '</a></span>';
//
//             $(this).html(html);
//         }
//
//     });
//
//     $(".readmorelink").click(function () {
//         if ($(this).hasClass("readless-content")) {
//             $(this).removeClass("readless-content");
//             $(this).html(moretext);
//         } else {
//             $(this).addClass("readless-content");
//             $(this).html(lesstext);
//         }
//         $(this).parent().prev().toggle(300);
//         $(this).prev().toggle(300);
//         return false;
//     });
// });

$(document).ready(function() {
    // Configure/customize these variables.
    var showchar = 100;  // How many characters are shown by default
    var ellipsestext = "...";
    var moretext = "Read more <i class='fa fa-caret-down'></i>";
    var lesstext = "Read less <i class='fa fa-caret-up'></i>";


    $('.readmore').each(function() {
        var content = $(this).html();

        if(content.length > showchar) {

            var c = content.substr(0, showchar);
            var h = content.substr(showchar, content.length - showchar);

            var html = c + '<span class="readmoreellipses">' + ellipsestext+ '&nbsp;</span><span class="readmorecontent"><span>'
                + h + '</span>&nbsp;&nbsp;<a href="" class="readmorelink">' + moretext + '</a></span>';

            $(this).html(html);
        }

    });

    $(".readmorelink").click(function(){
        if($(this).hasClass("readless")) {
            $(this).removeClass("readless");
            $(this).html(moretext);
        } else {
            $(this).addClass("readless");
            $(this).html(lesstext);
        }
        $(this).parent().prev().toggle();
        $(this).prev().toggle(300).css('display', 'inline');
        return false;
    });
});