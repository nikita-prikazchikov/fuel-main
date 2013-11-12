'use strict';

angular.module('testresult', ['testresultServices','testresultFilters']).
    config(['$routeProvider', function($routeProvider) {
        $routeProvider
            .when('/view', {templateUrl: 'partials/view.html',   controller: TestResultCtrl})
            .when('/tests', {templateUrl: 'partials/tests.html', controller: TestResultCtrl})
            .otherwise({redirectTo: '/view'});
    }]);