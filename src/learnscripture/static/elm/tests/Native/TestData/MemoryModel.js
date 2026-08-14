var _user$project$Native_TestData_MemoryModel = function () {
    var fs = require('fs');
    var path = require('path');
    var jsonPath = path.join(__dirname, '..', '..', '..', '..', '..', '..', 'tests', 'memorymodel_test_data.json');
    var memoryModelTestData = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
    var strengthEstimateTestData = memoryModelTestData['strengthEstimateTestData'];
    return {
        strengthEstimateTestData: strengthEstimateTestData
    }
}();
