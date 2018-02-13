import CalHeatMap = require('cal-heatmap');
import 'cal-heatmap/cal-heatmap.css';

var calHeatMapData = null;
var calHeatMapInstance = null;
var saveHeatmapPreferencesTimeout = null;

var setupCalendarHeatmap = function() {
    if ($('#id-heatmap-div').length == 0) {
        return;
    }
    if (!getHeatmapSection().is(':visible')) {
        // delay loading of data until we need it, which saves loading it at all
        // if the user has selected to collapse this section.
        return;
    }
    if (calHeatMapData == null) {
        $.ajax({
            url: $("#id-dashboard-script-data").attr('data-user-stats-verses-timeline-stats-csv-url') + "?r=" + Math.floor(Math.random() * 1000000000).toString(),
            success: function(data) {
                var allRows = data.replace(/\r/, '').trim().split(/\n/).map(r => r.split(/,/));
                var headers = allRows[0];
                var dataRows = allRows.slice(1);
                var final = [];
                for (var i = 0; i < dataRows.length; i++) {
                    var d = {};
                    for (var j = 0; j < headers.length; j++) {
                        d[headers[j]] = dataRows[i][j];
                    }
                    final.push(d);
                }
                calHeatMapData = final;
                createOrRefreshCalendarHeatmap(calHeatMapData);
                setupCalendarControls();
            }
        });
    } else {
        createOrRefreshCalendarHeatmap(calHeatMapData);
    }
}

var getSelectedStat = function() {
    return $('#id-heatmap-stat-selector .active a').attr('data-heatmap-select-stat');
}

var createOrRefreshCalendarHeatmap = function(allData) {
    // calculate dict in form required by CalHeatMap. Also calculate streaks,
    // relying on fact that data has zeros in it and is sorted correctly.
    var selectedStat = getSelectedStat();

    var stats = {};
    var biggestStreak = 0;
    var currentStreak = 0;
    for (var i = 0; i < allData.length; i++) {
        var ts = Date.parse(allData[i]['Date']) / 1000;
        var num = parseInt(allData[i][selectedStat], 10)
        stats[ts] = num;
        if (num == 0) {
            if (currentStreak > biggestStreak) {
                biggestStreak = currentStreak;
            }
            currentStreak = 0;
        } else {
            currentStreak += 1;
        }
    }
    if (currentStreak > biggestStreak) {
        biggestStreak = currentStreak;
    }
    $('#id-current-streak').text(currentStreak.toString() + " " + (currentStreak == 1 ? "day" : "days"));
    $('#id-biggest-streak').text(biggestStreak.toString() + " " + (biggestStreak == 1 ? "day" : "days"));

    if (calHeatMapInstance == null) {
        calHeatMapInstance = new CalHeatMap();
        var today = new Date();
        var year = today.getUTCFullYear();
        var month = today.getUTCMonth();
        var dayOfMonth = today.getUTCDate();
        var utcToday = new Date(Date.UTC(year, month, dayOfMonth));
        // Go back 2 years, and then clip the left hand side
        // This gives the best results visually.
        var numberOfYears = 2;
        year -= numberOfYears;
        calHeatMapInstance.init({
            cellSize: 10, // need to change #id-heatmap-div height if this is changed.
            data: stats,
            displayLegend: false,
            domain: "month",
            domainLabelFormat: "%b %Y",
            itemSelector: '#id-heatmap-div',
            maxDate: utcToday,
            nextSelector: '#id-heatmap-next',
            previousSelector: '#id-heatmap-previous',
            range: numberOfYears * 12 + 1,
            start: new Date(year, month, 1),
            subDomainDateFormat: "%Y-%m-%d",
            legend: [0, 10, 20, 35, 55, 80],
            highlight: utcToday,
            afterLoadData: function(data) {
                $('#id-heatmap-loading').remove();
                return data;
            }
        });
    } else {
        calHeatMapInstance.update(stats);
    };
}

var setupCalendarControls = function() {
    $('#id-heatmap-div').on('click', 'svg rect', function(ev) {
        var candidates = ev.currentTarget.parentNode.childNodes;
        for (var i = 0; i < candidates.length; i++) {
            var node = candidates[i];
            if (node.nodeName == 'title') {
                $('#id-heatmap-domain-title').text(node.textContent);
            }
        }
    });

    $('[data-heatmap-select-stat]').on('click', function(ev) {
        ev.preventDefault();
        var $target = $(ev.target);
        $('#id-heatmap-stat-selector .active').each((idx, elem) => {
            $(elem).removeClass('active');
        });
        $target.parent('[data-heatmap-select-stat-parent]').addClass('active');
        createOrRefreshCalendarHeatmap(calHeatMapData);
        saveHeatmapPreferencesDelayed();
    });
}

var getHeatmapSection = function() {
    return $('#id-heatmap-section');
}

var saveHeatmapPreferencesDelayed = function() {
    if (saveHeatmapPreferencesTimeout != null) {
        // Cancel previous one
        window.clearTimeout(saveHeatmapPreferencesTimeout);
        saveHeatmapPreferencesTimeout = null;
    }
    saveHeatmapPreferencesTimeout = window.setTimeout(saveHeatmapPreferences,
        1000);
}

var saveHeatmapPreferences = function() {
    $.ajax({
        url: '/api/learnscripture/v1/savemiscpreferences/?format=json',
        dataType: 'json',
        type: 'POST',
        data: {
            heatmap_default_stats_type: getSelectedStat(),
            heatmap_default_show: getHeatmapSection().is(':visible') ? 'true' : 'false'
        }
    })
};


var setupDashboardControls = function() {
    if (document.location.pathname.match(/\/dashboard/) === null) {
        return;
    }
    $("input[name=clearbiblequeue]").click(function(ev) {
        if (!confirm("This will remove chosen verses from your queue " +
            "for learning. To learn them you will have to " +
            "select the verses or verse sets again. " +
            "Continue?")) {
            ev.preventDefault();
        }
    });
    $("input[name=clearcatechismqueue]").click(function(ev) {
        if (!confirm("This will remove chosen catechism questions from " +
            "your queue for learning. To learn them you will have to " +
            "select the catechism again. " +
            "Continue?")) {
            ev.preventDefault();
        }
    });
    $("input[name=cancelpassage]").click(function(ev) {
        if (!confirm("This will cancel learning this passage in this version. " +
            "Any test scores will be saved. " +
            "Continue?")) {
            ev.preventDefault();
        }
    });
    setupCalendarHeatmap();

    $('#id-show-heatmap').on('click', function(ev) {
        ev.preventDefault();
        var $section = getHeatmapSection();
        var $icon = $('#id-show-heatmap i');
        if ($section.is(':visible')) {
            // Collapse
            $section.hide();
            $icon.removeClass('icon-heatmap-expanded').addClass('icon-heatmap-collapsed');
        } else {
            // Expand
            $section.show();
            $icon.removeClass('icon-heatmap-collapsed').addClass('icon-heatmap-expanded');
            if (calHeatMapData == null) {
                setupCalendarHeatmap();
            }
        }
        saveHeatmapPreferencesDelayed();
    })
};

$(document).ready(function() {
    setupDashboardControls();
});
