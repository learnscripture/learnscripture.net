var _user$project$Native_StringUtils = function () {
    // This is rather hard to rewrite with an efficient implementation in Elm's
    // functional style.
    var damerauLevenshteinDistance = function(a, b) {

        var INF = a.length + b.length;
        var i, j, d, i1, j1;
        var H = [];
        // Make matrix of dimensions a.length + 2, b.length + 2
        for (i = 0; i < a.length + 2; i++) {
            H.push(new Array(b.length + 2));
        }
        // Fill matrix
        H[0][0] = INF;
        for (i = 0; i <= a.length; ++i) {
            H[i + 1][1] = i;
            H[i + 1][0] = INF;
        }
        for (j = 0; j <= b.length; ++j) {
            H[1][j + 1] = j;
            H[0][j + 1] = INF;
        }
        var DA = {};
        for (d = 0; d < (a + b).length; d++) {
            DA[(a + b)[d]] = 0;
        }
        for (i = 1; i <= a.length; ++i) {
            var DB = 0;
            for (j = 1; j <= b.length; ++j) {
                i1 = DA[b[j - 1]];
                j1 = DB;
                d = ((a[i - 1] === b[j - 1]) ? 0 : 1);
                if (d === 0) {
                    DB = j;
                }
                H[i + 1][j + 1] = Math.min(H[i][j] + d,
                                           H[i + 1][j] + 1,
                                           H[i][j + 1] + 1,
                                           H[i1][j1] + (i - i1 - 1) + 1 + (j - j1 - 1));
            }
            DA[a[i - 1]] = i;
        }
        return H[a.length + 1][b.length + 1];
    }
    return {
        damerauLevenshteinDistance: F2(damerauLevenshteinDistance)
    };
}();

