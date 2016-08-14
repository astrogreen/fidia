
var app = angular.module("DCApp", [ "isteven-multi-select", 'ngSanitize', 'ngCookies'])
.config(['$cookiesProvider', function($cookiesProvider) {
    // Set $cookies defaults
    $cookiesProvider.defaults.path = '/';
    // $cookiesProvider.defaults.secure = true;
    // $cookiesProvider.defaults.expires = exp_date;
    // $cookiesProvider.defaults.domain = '/asvo/';
}])
.config(['$httpProvider', function($httpProvider) {
    //
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
}]);
