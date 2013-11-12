'use strict';

/* Controllers */

function TestResultCtrl($scope, $routeParams, $location, TestResult) {

    $scope.statusList = [];
    $scope.environmentList = [];
    $scope.tags = [];
    $scope.statusListForEnvironments = [];

    $scope.testCaseList = TestResult.query(function(){
        var list = $scope.testCaseList;

        list.forEach(function(item){
            if ( $scope.statusList.indexOf(item.status) == -1 ){
                $scope.statusList.push(item.status);
            }
            if ( $scope.environmentList.indexOf(item.environment) == -1 ){
                $scope.environmentList.push(item.environment);
            }
            $scope.tags = _.union($scope.tags, item.tags);
        });

        for ( var e = 0; e < $scope.environmentList.length; e ++ ){
            for ( var i = 0; i < $scope.statusList.length; i ++ ){
                $scope.statusListForEnvironments.push(
                    {
                        environment:$scope.environmentList[e],
                        status:$scope.statusList[i]
                    }
                );
            }
        }

    });

    $scope.testCaseFilter = {};
    $scope.testCaseFilter.status = $location.search().status || "";
    $scope.testCaseFilter.tag = $location.search().tag || "";

    $scope.setTestCase=function(testCase){
        $scope.testCase = testCase;
    };

    $scope.fixValue=function(value){
        return value == null ? '': value;
    };

    $scope.showDetails = function( status, tag, environment ){
        alert("status: " + status + " tag: " + tag + " env: " + environment );
//        $location.search("status", status ? status : "" );
//        $location.search("tag", tag ? tag : "" );
//        $location.search("environment", environment ? environment : "" );
//        $location.path("/tests");
    };

//    $scope.showLog = function (testCase) {
//        var d = $dialog.dialog({
//                backdrop: true,
//                keyboard: true,
//                backdropClick: true,
//                templateUrl: "partials/log.html",
//                controller: 'DialogController',
//                dialogClass: "modal full-height big",
//                resolve:{
//                    testCase:function(){return testCase}
//                }
//            }
//        );
//        d.open();
//    }
}

function DialogController($scope, dialog, testCase) {

    $scope.testCase = testCase;
    $scope.testStepList = eval(testCase.log);
    $scope.testStepId = 0;

    $scope.close = function () {
        dialog.close();
    };
}