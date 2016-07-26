console.log('directives.js');
(function(angular){
    "use strict";

    var app = angular.module('DCApp');

    // Style new disabled button
    function disableAddButton (elem){
        // disable the add button
        elem.html('<i class="fa fa-check"></i>')
            .removeClass('btn-primary')
            .attr('disabled', true);
    }

    function disableFormatDropdown(elem){
        // disable the format button
        elem.html('Added')
            .removeClass('btn-primary')
            .attr('disabled', true);
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
                formats: "=",
            },
            replace: true,
            templateUrl: '/static/download/js/templates/add-download-button.html',
            link: function(scope, elem, attr){

                // define targets on scope.
                scope.add_button = angular.element(elem[0].querySelector('.add-button'));
                scope.format_dropdown_button = angular.element(elem[0].querySelector('.format-dropdown button'));
                scope.format_dropdown_li = angular.element(elem[0].querySelector('.format-dropdown ul li'));
                // populate the dropdown
                scope.populateDropdown = function(){
                    if (typeof attr.formats !== 'undefined' && attr.formats.length > 0){
                        scope.formats = JSON.parse(attr.formats);
                    };
                };

                scope.constructItem = function() {
                    // Construct the item object (on the local scope) from the element attributes
                    // DO THIS ONLY ONCE
                    scope.item = {};
                    if (typeof attr.url !== 'undefined') {
                        scope.item['id'] = attr.url;
                        if (typeof attr.options !== 'undefined') {
                            scope.item['options'] = attr.options;
                        }
                        if (typeof attr.formats !== 'undefined') {
                            //    this won't have been set yet.
                            scope.item['format'] = '';
                        }
                    } else {
                        scope.item['id'] = 'Error. Cannot find id (url) has been set for this add-to-download-directive. Please contact the site administrator. '
                    }
                };

                angular.element(document).ready(function() {
                    scope.populateDropdown();
                    scope.constructItem();

                    var saved_items = DownloadService.checkItemInCookie();

                    // CHECK for this in cookie already and disable the button.
                    if (undefined != saved_items){
                        for (var i = 0; i < saved_items.length; i++) {
                            if (undefined != scope.formats){
                                for (var j = 0; j < scope.formats.length; j++){
                                    var temp = scope.item['id']+'?format='+scope.formats[j];
                                    if (saved_items[i] == temp){
                                        // IF this url with this format is in the cart,
                                        // then say this piece of data has been added already
                                        // scope.formats.splice(j,1);
                                        // scope.$apply();
                                        disableAddButton(scope.add_button);
                                        disableFormatDropdown(scope.format_dropdown_button);
                                    }
                                }
                            } else {
                                if (saved_items[i] == scope.item['id']){
                                    disableAddButton(scope.add_button);
                                    disableFormatDropdown(scope.format_dropdown_button);
                                }
                            }
                        }
                    }
                });

                scope.addItem = function(){
                    // Lock in format
                    if (scope.item['format']){
                        var temp = scope.item['id'];
                        // ?format=type
                        scope.item['id'] = temp+'?format='+scope.item['format'];
                    }

                    // Pass the item into the addItem method of DownloadService
                    // populate the items obj for this particular view before start writing in to the cookie
                    DownloadService.getItems();
                    DownloadService.addItem(scope.item);
                    DownloadService.getItemCount();

                    $('#mini-download').addClass('bounce')
                        .one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function(){
                            $('#mini-download').removeClass('bounce');
                        });

                    //disable the buttons
                    disableAddButton(scope.add_button);
                    disableFormatDropdown(scope.format_dropdown_button);
                };

                scope.chooseFormat = function(f){
                    scope.item['format'] = f;
                };


            }
        }
    });

})(window.angular)