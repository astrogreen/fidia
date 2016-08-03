console.log('directives.js');
(function(angular){
    "use strict";

    var app = angular.module('DCApp');

    function caretToTick(elem){
        // Switch caret for green tick
        elem.html('<i class="fa fa-check text-success"></i>');
    }

    function disableFormat(elem, format){
        elem.html(format + '<small class="sub-heading"> ADDED</small>')
            .attr('disabled', true)
            .addClass('disabled')
            .parent('li').addClass('disabled');
    }

    // DownloadDirective
    app.directive('miniDownload', function(DownloadService){
        return{
            // Create in an isolated scope
            scope:{
            },
            restrict: 'AE',
            replace: true,
            templateUrl: '/static/download/js/templates/mini-download.html',
            link: function(scope, elem, attr){
                scope.getItemCount = function(){
                    // Returns the item count from the Download Service
                    return DownloadService.getItemCount();
                }
            }
        };
    });

    app.directive('addDownloadButton', function(DownloadService, $filter){
        return {
            // E for Element
            // A for Attribute
            // C for Class
            // e.g., by adding a restrict property with the value "A", the directive can only be invoked by attributes.
            restrict: 'E',
            scope: {
                // 3 types of bindings for scope properties
                // @ == string
                // & == one-way binding
                // = == two-way binding
                formats: "="
            },
            replace: true,
            templateUrl: '/static/download/js/templates/add-download-button.html',
            link: function(scope, elem, attr){

                // define targets on scope.
                scope.caret_button = angular.element(elem[0].querySelector('.add-to-download-caret'));

                // populate the dropdown
                scope.populateDropdown = function(){
                    if (typeof attr.formats !== 'undefined' && attr.formats.length > 0){
                        scope.formats = JSON.parse(attr.formats);
                    };
                };

                scope.constructItem = function() {
                    // DO THIS ONLY ONCE

                    // Construct an item per format (on the local scope) from the element attributes
                    // items = {format: item, format: item}
                    if (typeof attr.url !== 'undefined' && typeof scope.formats !== 'undefined') {
                        scope.items = {};

                        var lastChar = attr.url.substr(-1);     // Selects the last character
                        if (lastChar != '/') {                  // If the last character is not a slash
                           attr.url = attr.url + '/';           // Append a slash to it.
                        }
                        for (var f = 0; f< scope.formats.length; f++){
                            // Create temp item, append the format type
                            var item ={};
                            var temp = attr.url;
                            // ?format=type
                            item['id']=temp+'?format='+scope.formats[f];
                            item['options'] = attr.options;
                            item['format'] = scope.formats[f];
                            scope.items[scope.formats[f]] = item;
                        }

                    } else {
                        console.log('Error. Cannot find id (url) has been set for this add-to-download-' +
                            'directive. Please contact the site administrator. ');
                    }
                };

                angular.element(document).ready(function() {
                    scope.populateDropdown();
                    scope.constructItem();

                    var saved_items = DownloadService.checkItemInCookie();

                    // CHECK for this in cookie already and disable the button.
                    if (undefined != saved_items){
                        for (var i = 0; i < saved_items.length; i++) {
                            // console.log(saved_items[i]);
                            if (undefined != scope.formats){
                                angular.forEach(scope.items, function(v, k){
                                    var temp = v['id'];
                                    if (saved_items[i] == temp){
                                        // Already in cart, disable this element
                                        var format = v['format'];
                                        caretToTick(scope.caret_button);
                                        scope.format_dropdown = angular.element(elem[0].querySelector("ul.dropdown-menu li ."+format));
                                        disableFormat(scope.format_dropdown, format);

                                    } else {

                                    }
                                });
                            }
                        }
                    }
                });

                scope.addItem = function(f){
                    // Get clicked item from scope.items by format
                    scope.item = scope.items[f];
                    console.log(scope.item);
                    // Pass the item into the addItem method of DownloadService
                    // populate the items obj for this particular view before start writing in to the cookie
                    DownloadService.getItems();
                    DownloadService.addItem(scope.item);
                    DownloadService.getItemCount();

                    $('#mini-download').addClass('bounce')
                        .one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function(){
                            $('#mini-download').removeClass('bounce');
                        });

                    // Change button states
                    // disableAddButton(scope.add_button);
                    // disableFormatDropdown(scope.format_dropdown_button);
                    caretToTick(scope.caret_button);

                    scope.format_dropdown = angular.element(elem[0].querySelector("ul.dropdown-menu li ."+f));

                    disableFormat(scope.format_dropdown, f);

                    // angular.element(elem[0].querySelector(".dropdown-menu ul li ."+f))
                    //     .html('added')
                };

                scope.chooseFormat = function(f){
                    scope.item['format'] = f;
                };


            }
        }
    });

    // DownloadDirective
    app.directive('sampleDownload', function(DownloadService){
        return{
            // Create in an isolated scope
            scope:{
            },
            restrict: 'AE',
            replace: true,
            templateUrl: '/static/download/js/templates/sample-download.html',
            link: function(scope, elem, attr){
                // Does nothing yet...
            }
        };
    });

})(window.angular);