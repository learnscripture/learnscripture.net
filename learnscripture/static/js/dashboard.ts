import CalHeatMap = require('cal-heatmap');
import 'cal-heatmap/cal-heatmap.css';

import { UAParser } from 'ua-parser-js';
import { getSavedCalls } from './offlineutils';

var calHeatMapData: null | any[] = null;
var streaksCaptions: null | any = null;
var calHeatMapInstance: null | any;
var saveHeatmapPreferencesTimeout: null | number = null;

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
            url: '/api/learnscripture/v1/usertimelinestats/?format=json',
            dataType: 'json',
            type: 'GET',
            data: {
                username: $("#id-dashboard-script-data").attr('data-user-timeline-stats-user')
            },
            success: function(data) {
                var allRows = data['stats'].replace(/\r/, '').trim().split(/\n/).map(r => r.split(/,/));
                var headers = allRows[0];
                var dataRows = allRows.slice(1);
                var final: any[] = [];
                for (var i = 0; i < dataRows.length; i++) {
                    var d = {};
                    for (var j = 0; j < headers.length; j++) {
                        d[headers[j]] = dataRows[i][j];
                    }
                    final.push(d);
                }
                calHeatMapData = final;
                streaksCaptions = data['streaks_formatted'];
                createOrRefreshCalendarHeatmap(calHeatMapData, streaksCaptions);
                setupCalendarControls();
            }
        });
    } else {
        createOrRefreshCalendarHeatmap(calHeatMapData, streaksCaptions);
    }
}

var getSelectedStat = function() {
    return $('#id-heatmap-stat-selector input[name=stat]:checked').val() as string;
}

var createOrRefreshCalendarHeatmap = function(allData, streaks) {
    var selectedStat = getSelectedStat();

    if (streaks !== null) {
        $('#id-current-streak').text(streaks[selectedStat]['current']);
        $('#id-biggest-streak').text(streaks[selectedStat]['biggest']);
    }
    // calculate dict in form required by CalHeatMap.
    var stats = {};
    for (var i = 0; i < allData.length; i++) {
        var ts = Date.parse(allData[i]['Date']) / 1000;
        var num = parseInt(allData[i][selectedStat], 10)
        stats[ts] = num;
    }

    if (calHeatMapInstance == null) {
        calHeatMapInstance = new CalHeatMap();
        var today = new Date();
        var year = today.getUTCFullYear();
        var month = today.getUTCMonth();
        var dayOfMonth = today.getUTCDate();
        var utcToday = new Date(year, month, dayOfMonth);
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

    $('#id-heatmap-stat-selector input').on('change', function(ev) {
        createOrRefreshCalendarHeatmap(calHeatMapData, streaksCaptions);
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
            $icon.removeClass('expanded');
        } else {
            // Expand
            $section.show();
            $icon.addClass('expanded');
            if (calHeatMapData == null) {
                setupCalendarHeatmap();
            }
        }
        saveHeatmapPreferencesDelayed();
    })

    if (getSavedCalls().length > 0) {
        $("#id-unfinished-session-warning").show();
        $("#id-unfinished-session-unsaved-data-warning").show();
    }

    var parser = new UAParser();
    if (parser.getOS().name == "Android" && parser.getBrowser().name == "Firefox") {
        // NB not 'show()' below, we need the CSS query for 'standalone' to work.
        $('#id-firefox-homescreen-install-prompt').removeClass("hide");
    }
};

$(document).ready(function() {
    setupDashboardControls();
});
