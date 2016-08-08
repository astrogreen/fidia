$(document).ready(function() {
    var readmoretext = '<span class="readmore_link">...<a href="" >Read more <i class="fa fa-caret-down"></i></a></span>';
    var readlesstext = '<span class="readmore_link">...<a href="" >Read less <i class="fa fa-caret-up"></i></a></span>';
    readmorelimit = 200;

    $('.readmore').each(function() {
        // if this element contains less than readmorelimit, remove the readmore class
        var content = $(this).html();
        if(content.length < readmorelimit) {
            $(this).removeClass('readmore');
        } else {
            $(this).append(readmoretext);
        }
    });

     $(".readmore_link > a").click(function(){
        if($(this).closest('.readmore').hasClass("readless")) {
            $(this).closest('.readmore').removeClass("readless");
            $(this).closest('.readmore').css('max-height',"87px");
            $(this).html(readmoretext)
        } else {
            $(this).closest('.readmore').addClass("readless");
            $(this).closest('.readmore').css('max-height',"none");
            $(this).html(readlesstext)
        }
        return false;
    });
});


