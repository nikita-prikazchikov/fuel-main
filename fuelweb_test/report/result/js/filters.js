var testResultModule = angular.module('testresultFilters', []);

testResultModule.filter("getResult",function(){
    return function(condition, trueResult, falseResult){
        return condition ? trueResult : falseResult;
    }
});
testResultModule.filter("showTime",function(){
    return function(seconds){
        var hours, minutes, str = "";
        hours = Math.floor(seconds / 3600);
        if ( hours ){
            seconds -= hours * 3600;
            str += hours + " h "
        }
        minutes = Math.floor(seconds / 60);
        if ( minutes ){
            seconds -= minutes * 60;
            str += minutes + " min "
        }
        str += Math.floor( seconds ) + " s";
        return str;
    }
});
testResultModule.filter('unique',function(){
    return function(items,field){
        var ret = [], found={};
        for(var i in items){
            var item = items[i][field];
            if(!found[item]){
                found[item]=true;
                ret.push(items[i]);
            }
        }
        return ret;
    }
});
