// IIFE: Immediately invoked function expression: (function(){})() (where window == global scope)
// Create a download service
(function(angular){
   // Force variable declarations
    "use strict";

    // turn off for dev:
    // console.log = function() {};

    console.log('services.js');

    var app = angular.module('DCApp');

    // Inject in $cookieStore
    app.factory('DownloadService', function($cookieStore){

        // Private items object
        var items = {};

        function checkCookie(){
            console.log('- - CHECK - - - - ');
            if(items.length) {
                console.log('- - Items: ', items)
            }
            if (undefined != $cookieStore){
                    console.log('- - Cookie: ', $cookieStore.get('items'));
            } else {
                console.log('- - Cookie Empty!')
            }
        }

        // Update cookies
        function updateItemsCookie(){
            console.log('updateItemsCookie: ', items);
            // checkCookie();
            // Initialize an object that will be saved as a cookie
            var itemsCookie = {};
            // Loop through the items in the download
            angular.forEach(items, function(item, key){
                // Add each item to the items cookie,
                // using the id as the identifier
                itemsCookie[key] = item;
            });
            // Use the $cookieStore service to persist the itemsCookie object to the cookie named 'items'
            $cookieStore.put('items', itemsCookie);
            checkCookie();
        }

        function removeFromArray(array, elem){
            for(var i = array.length-1; i--;){
                if (array[i] === elem) array.splice(i, 1);
            }
        }

        function cleanArray(array){
            var remove_arr = [document.domain, document.domain+':'+location.port, location.protocol, 'asvo', "", '', ];
            for(var j = 0; j < remove_arr.length; j++){
                removeFromArray(array,remove_arr[j]);
            }
        }

        function objExists(arr, elem, property) {
          return arr.some(function(el) {
            return el[property] === elem;
          });
        }


        // Angular factories return service objects
        return {

            getItems: function() {
                // Initialize the itemsCookie variable
                var itemsCookie;

                // checkCookie();

                // Check if download is empty, if not - populate the current service with the cookie items
                if(!items.length) {
                    // Get the items cookie
                    itemsCookie = $cookieStore.get('items');
                    // Check if the item cookie exists
                    if(itemsCookie) {
                        // Loop through the items in the cookie
                        angular.forEach(itemsCookie, function(item, key) {
                            // Get the product details from the ProductService using the guid
                            items[item.id] = item;
                        });
                    }
                }
                // Returns items object
                return items;
            },

            checkItemInCookie: function(){
                // share data between services
                if (undefined != $cookieStore){
                    var saved_items = [];
                    angular.forEach($cookieStore.get('items'), function(cookieitem){
                        saved_items.push(cookieitem.id);
                    });
                    return saved_items;
                }
            },

            addItem: function(item){
                // Check if item already exists
                // If exists - don't add
                // Else, push the item onto the items array, at the relevant astronomical object key
                if (!items[item.id]){
                    // TODO strip the item.id field once added as already present in key - this might affect other services
                    items[item.id] = item;

                } else {
                    // nothing - we don't need to update quantity - but this will need altering to cope with AO structure
                }
                // Update cookie
                updateItemsCookie();
                // Update angular summary obj
                this.getSummary();
            },

            removeItem: function(id){
                // Remove an item from the items object
                delete items[id];
                // Update cookie
                updateItemsCookie();
            },

            emptyDownload: function(){
                // items = {};
                // Can't re-initialize items object to an empty object, else break the reference and ng-repeat won't update
                // Instead, loop and clear the items object

                for (var prop in items){
                    delete items[prop]
                }
                // Remove items cookie using $cookieStore
                $cookieStore.remove('items');

                // updateItemsCookie();
                // checkCookie();
            },

            getItemCount: function(){
                // Initialize total counter
                var total = 0;
                // Loop through items and increment the total - also count by survey and unique objects
                // angular.forEach(items, function(item){
                //     // total += parseInt(item.quantity)
                //     total += 1;
                // })
                // console.log('getItemCount ', total)

                // NO! Best to use the updated cookie here - so the directive can use this method (directive doesn't have access to controller scope)
                if (undefined != $cookieStore){
                    angular.forEach($cookieStore.get('items'), function(item){
                        // total += parseInt(item.quantity)
                        total += 1;
                    })
                }
                return total;
            },

            prettifyCookie: function(items){

                var prettyCookie = {};
                prettyCookie["objects"] = {}, prettyCookie["samples"] = {};
                // object, id: prettified array
                angular.forEach(items, function(v, url){
                    // Clean the url, removing all excess info (protocol, domain etc) and split into arr
                    var url_arr = url.split("/");
                    cleanArray(url_arr);
                    var data_obj = {}, temp = [];

                    // If the url has come from the data browser, this will be a single object.
                    if (url.indexOf("data-browser") !== -1){

                        // Knowing that the 1 and 2 elements will always be sample and ao, we can
                        // predefine these for the view.
                        // Though this isn't actually asserted... it should be.
                        data_obj['url'] = url.split('?format=')[0];

                        data_obj['sample'] = url_arr[1].toUpperCase();
                        data_obj['ao'] = url_arr[2];
                        data_obj['id'] = url;
                        data_obj['options'] = v.options;

                        if (url_arr[url_arr.length-1].indexOf('?format=') > -1){
                        // If a format exists on the last element of the array, pop it off
                        // and prettify
                            data_obj['format'] = url_arr[url_arr.length-1].split('?format=')[1];
                            url_arr.pop();
                        }
                        // Collect the remaining data pieces below trait into one line
                        for(var i = 3; i < url_arr.length; i++) {
                            if(url_arr[i]!=="" && url_arr[i]!==''){
                                temp.push(url_arr[i]);
                            }
                        }
                        data_obj['trait'] = temp;
                        prettyCookie["objects"][url] = data_obj;

                    } else if (url.indexOf("query-history") !== -1){
                        // If the url has come from the query builder - this will have options
                        data_obj['url'] = url;
                        data_obj['id'] = url;
                        data_obj['sample_id'] = url.split("query-history/")[1].split("/")[0];
                        // data_obj['options'] = JSON.parse(v.options);
                        data_obj['options'] = v.options;
                        prettyCookie["samples"][url] = data_obj;
                    }


                });
                return prettyCookie;
            },

            getSummary: function(prettifiedCookie){

                var summary = {
                    "bySample": [
                            // {"sample": "GAMA", "count": 3},
                        ],
                        "byObject": [
                            // {"id": 1, "name": "John Doe"},
                        ],
                        "byData": [
                            // {"id": 1, "name": "John Doe"},
                        ],
                };
                var itemsCookie = this.prettifyCookie(this.getItems());

                angular.forEach(itemsCookie.objects, function(val, key){
                    // bySample
                    var sample_str = val.sample;

                    if (objExists(summary.bySample, sample_str, 'sample') == true){
                        // if the object exists in the sample structure already
                        // find it and boost the count.
                        for (var i=0;i<summary.bySample.length;i++){
                            if (summary.bySample[i].sample == sample_str){
                                summary.bySample[i]["count"] = summary.bySample[i]["count"]+1;
                            }
                        }
                    } else {
                        summary.bySample.push({"sample": sample_str, "count": 1})
                    }
                    // byObject
                    var object_str = val.ao;
                    if (objExists(summary.byObject, object_str, 'ao') == true){
                        // if the object exists in the ao structure already
                        // find it and boost the count.
                        for (var j=0;j<summary.byObject.length;j++){
                            if (summary.byObject[j].ao == object_str){
                                summary.byObject[j]["count"] = summary.byObject[j]["count"]+1;
                            }
                        }
                    } else {
                        summary.byObject.push({"ao": object_str, "count": 1})
                    }
                });

                return summary;
            },

            download: function(){
                // TODO This function should create a valid json and save in user's download history
                // Wrap up (pretty==more info attached) cookie and return a string of valid JSON
                var download_arr = this.prettifyCookie(this.getItems());
                // console.log(download_arr);
                return JSON.stringify(download_arr);
            }

            // user clicks button format appended to url.


        }
    })

    app.factory('StorageService', function($http){

        // Private items object
        var items = {};

        function checkStorage(){
            console.log('- - CHECK - - - - ');
            if(items.length) {
                console.log('- - Items: ', items)
            }
            if (undefined != $cookieStore){
                    console.log('- - Cookie: ', $cookieStore.get('items'));
            } else {
                console.log('- - Cookie Empty!')
            }
        }

        // Update cookies
        function updateItemsCookie(){
            console.log('updateItemsCookie: ', items);
            // checkCookie();
            // Initialize an object that will be saved as a cookie
            var itemsCookie = {};
            // Loop through the items in the download
            angular.forEach(items, function(item, key){
                // Add each item to the items cookie,
                // using the id as the identifier
                itemsCookie[key] = item;
            });
            // Use the $cookieStore service to persist the itemsCookie object to the cookie named 'items'
            $cookieStore.put('items', itemsCookie);
            checkCookie();
        }

        function removeFromArray(array, elem){
            for(var i = array.length-1; i--;){
                if (array[i] === elem) array.splice(i, 1);
            }
        }

        function cleanArray(array){
            var remove_arr = [document.domain, document.domain+':'+location.port, location.protocol, 'asvo', "", '', ];
            for(var j = 0; j < remove_arr.length; j++){
                removeFromArray(array,remove_arr[j]);
            }
        }

        function objExists(arr, elem, property) {
          return arr.some(function(el) {
            return el[property] === elem;
          });
        }


        // Angular factories return service objects
        return {

            getStorageContents: function(url) {
                // Check if scope items is empty, if not - populate the current service with the storage data
                if(!items.length) {
                    // then returns a new promise, which we return - the new promise is resolved
                    // via response.data
                    return $http.get(url).then(function (response) {
                        // Check if the item cookie exists
                        if(response.data.storage_data) {
                            var storage_data = JSON.parse(response.data.storage_data);
                            // Loop through the items in the cookie
                            angular.forEach(storage_data, function(item, key) {
                                // everything is stored by unique ID
                                items[item.id] = item;
                            });
                        }
                        return items;
                        // return response.data;
                    });
                }
                // Returns items object
                return items;
            },

            // getItems: function() {
            //     // Initialize the itemsCookie variable
            //     var itemsCookie;
            //
            //     // checkCookie();
            //
            //     // Check if download is empty, if not - populate the current service with the cookie items
            //     if(!items.length) {
            //         // Get the items cookie
            //         itemsCookie = $cookieStore.get('items');
            //         // Check if the item cookie exists
            //         if(itemsCookie) {
            //             // Loop through the items in the cookie
            //             angular.forEach(itemsCookie, function(item, key) {
            //                 // Get the product details from the ProductService using the guid
            //                 items[item.id] = item;
            //             });
            //         }
            //     }
            //     // Returns items object
            //     return items;
            // },
            //
            // checkItemInCookie: function(){
            //     // share data between services
            //     if (undefined != $cookieStore){
            //         var saved_items = [];
            //         angular.forEach($cookieStore.get('items'), function(cookieitem){
            //             saved_items.push(cookieitem.id);
            //         });
            //         return saved_items;
            //     }
            // },
            //
            // addItem: function(item){
            //     // Check if item already exists
            //     // If exists - don't add
            //     // Else, push the item onto the items array, at the relevant astronomical object key
            //     if (!items[item.id]){
            //         // TODO strip the item.id field once added as already present in key - this might affect other services
            //         items[item.id] = item;
            //
            //     } else {
            //         // nothing - we don't need to update quantity - but this will need altering to cope with AO structure
            //     }
            //     // Update cookie
            //     updateItemsCookie();
            //     // Update angular summary obj
            //     this.getSummary();
            // },
            //
            // removeItem: function(id){
            //     // Remove an item from the items object
            //     delete items[id];
            //     // Update cookie
            //     updateItemsCookie();
            // },
            //
            // emptyDownload: function(){
            //     // items = {};
            //     // Can't re-initialize items object to an empty object, else break the reference and ng-repeat won't update
            //     // Instead, loop and clear the items object
            //
            //     for (var prop in items){
            //         delete items[prop]
            //     }
            //     // Remove items cookie using $cookieStore
            //     $cookieStore.remove('items');
            //
            //     // updateItemsCookie();
            //     // checkCookie();
            // },
            //
            // getItemCount: function(){
            //     // Initialize total counter
            //     var total = 0;
            //     // Loop through items and increment the total - also count by survey and unique objects
            //     // angular.forEach(items, function(item){
            //     //     // total += parseInt(item.quantity)
            //     //     total += 1;
            //     // })
            //     // console.log('getItemCount ', total)
            //
            //     // NO! Best to use the updated cookie here - so the directive can use this method (directive doesn't have access to controller scope)
            //     if (undefined != $cookieStore){
            //         angular.forEach($cookieStore.get('items'), function(item){
            //             // total += parseInt(item.quantity)
            //             total += 1;
            //         })
            //     }
            //     return total;
            // },
            //

            prettifyData: function(items){
                /**
                 * Takes an object and returns the pretty version for the template rendering
                 * @param {Object} items
                 * @return {Object} prettyData
                 */

                var prettyData = {};
                prettyData["objects"] = {}, prettyData["samples"] = {};
                // object, id: prettified array
                angular.forEach(items, function(v, url){
                    // Clean the url, removing all excess info (protocol, domain etc) and split into arr
                    var url_arr = url.split("/");
                    cleanArray(url_arr);
                    var data_obj = {}, temp = [];

                    // If the url has come from the data browser, this will be a single object.
                    if (url.indexOf("data-browser") !== -1){

                        // Knowing that the 1 and 2 elements will always be sample and ao, we can
                        // predefine these for the view.
                        // Though this isn't actually asserted... it should be.
                        data_obj['url'] = url.split('?format=')[0];

                        data_obj['sample'] = url_arr[1].toUpperCase();
                        data_obj['ao'] = url_arr[2];
                        data_obj['id'] = url;
                        data_obj['options'] = v.options;

                        if (url_arr[url_arr.length-1].indexOf('?format=') > -1){
                        // If a format exists on the last element of the array, pop it off
                        // and prettify
                            data_obj['format'] = url_arr[url_arr.length-1].split('?format=')[1];
                            url_arr.pop();
                        }
                        // Collect the remaining data pieces below trait into one line
                        for(var i = 3; i < url_arr.length; i++) {
                            if(url_arr[i]!=="" && url_arr[i]!==''){
                                temp.push(url_arr[i]);
                            }
                        }
                        data_obj['trait'] = temp;
                        prettyData["objects"][url] = data_obj;

                    } else if (url.indexOf("query-history") !== -1){
                        // If the url has come from the query builder - this will have options
                        data_obj['url'] = url;
                        data_obj['id'] = url;
                        data_obj['sample_id'] = url.split("query-history/")[1].split("/")[0];
                        // data_obj['options'] = JSON.parse(v.options);
                        data_obj['options'] = v.options;
                        prettyData["samples"][url] = data_obj;
                    }
                });
                return prettyData;
            },

            getSummary: function(data){

                var summary = {
                    "bySample": [
                            // {"sample": "GAMA", "count": 3},
                        ],
                        "byObject": [
                            // {"id": 1, "name": "John Doe"},
                        ],
                        "byData": [
                            // {"id": 1, "name": "John Doe"},
                        ],
                };

                var pretty_data = this.prettifyData(data);

                angular.forEach(pretty_data.objects, function(val, key){
                    // bySample
                    var sample_str = val.sample;

                    if (objExists(summary.bySample, sample_str, 'sample') == true){
                        // if the object exists in the sample structure already
                        // find it and boost the count.
                        for (var i=0;i<summary.bySample.length;i++){
                            if (summary.bySample[i].sample == sample_str){
                                summary.bySample[i]["count"] = summary.bySample[i]["count"]+1;
                            }
                        }
                    } else {
                        summary.bySample.push({"sample": sample_str, "count": 1})
                    }
                    // byObject
                    var object_str = val.ao;
                    if (objExists(summary.byObject, object_str, 'ao') == true){
                        // if the object exists in the ao structure already
                        // find it and boost the count.
                        for (var j=0;j<summary.byObject.length;j++){
                            if (summary.byObject[j].ao == object_str){
                                summary.byObject[j]["count"] = summary.byObject[j]["count"]+1;
                            }
                        }
                    } else {
                        summary.byObject.push({"ao": object_str, "count": 1})
                    }
                });
                console.log(angular.toJson(summary));
                return summary;
            },
            //
            // download: function(){
            //     // TODO This function should create a valid json and save in user's download history
            //     // Wrap up (pretty==more info attached) cookie and return a string of valid JSON
            //     var download_arr = this.prettifyCookie(this.getItems());
            //     console.log(download_arr);
            //     return JSON.stringify(download_arr);
            // }
            //
            // // user clicks button format appended to url.


        }
    })

})(window.angular);
