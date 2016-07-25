console.log('directives.js');
(function(angular){
    "use strict"

    var app = angular.module('DCApp');

    // Style new disabled button
    function disableAddDownloadButton (elem){
        // console.log('disable',elem);
        elem.addClass('btn-added-to-download')
            .html('<i class="fa fa-check"></i>')
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

    app.directive('addDownloadButton', function(DownloadService){
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
                // item: "@"
            },
            replace: true,
            templateUrl: '/static/download/js/templates/add-download-button.html',
            link: function(scope, elem, attr){

                // Construct the item object (on the local scope) from the element attributes
                scope.item = {};
                if (typeof attr.url !== 'undefined') {
                    scope.item['id'] = attr.url;
                    if (typeof attr.options !== 'undefined') {
                        scope.item['options'] = attr.options;
                    }
                } else {
                    scope.item['id'] = 'Error. Cannot find id (url) has been set for this add-to-download-directive. Please contact the site administrator. '
                }

                angular.element(document).ready(function() {
                    var saved_items = DownloadService.checkItemInCookie();

                    // CHECK for this in cookie already and disable the button.
                    if (undefined != saved_items){
                        for (var i = 0; i < saved_items.length; i++) {
                            if (saved_items[i] == scope.item['id']){
                                disableAddDownloadButton(elem);
                            }
                        }
                    }
                });

                scope.addItem = function(){
                    // Pass the item into the addItem method of DownloadService
                    // populate the items obj for this particular view before start writing in to the cookie
                    DownloadService.getItems();
                    DownloadService.addItem(scope.item);
                    DownloadService.getItemCount();
                },
                elem.bind('click', function(e){
                    // e.currentTarget is element that event is hooked on (target is the one that received the click)
                    disableAddDownloadButton(angular.element(e.currentTarget));

                    $('#mini-download').addClass('bounce')
                        .one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function(){
                            $('#mini-download').removeClass('bounce');
                        });
                })
            }
        }
    });

})(window.angular)