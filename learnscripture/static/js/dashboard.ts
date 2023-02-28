import CalHeatmap from 'cal-heatmap';

import 'cal-heatmap/cal-heatmap.css';

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
                        var val = dataRows[i][j];
                        d[headers[j]] = (!val.includes("-")) ? parseInt(val, 10) : val;
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

    if (calHeatMapInstance == null) {
        calHeatMapInstance = new CalHeatmap();
        calHeatMapInstance.on('fill', () => {
            $('#id-heatmap-loading').remove();
        });

        calHeatMapInstance.on('click', (event, timestamp: number, value) => {
            var d = new Date(timestamp);
            $('#id-heatmap-domain-title').text(d.toISOString().split('T')[0] + ": " + value.toString());

        })
    }
    var today = new Date();

    // Switch to UTC, which is what our stats are in
    var year = today.getUTCFullYear();
    var month = today.getUTCMonth();
    var dayOfMonth = today.getUTCDate();
    var utcToday = new Date(year, month, dayOfMonth);
    // To cope with different screens, we include lots of data
    // but clip the left hand side
    var rangeInYears = 1;
    var start = new Date(year - rangeInYears, month, dayOfMonth);
    calHeatMapInstance.paint({
        itemSelector: '#id-heatmap-div',
        range: 12 * rangeInYears + 1,
        date: {
            start: start,
            max: utcToday,
            highlight: utcToday,
        },
        data: {
            source: allData,
            x: "Date",
            y: selectedStat,
        },
        domain: {
            type: "month",
            label: {
                text: "MMM YYYY",
            },
        },
        subDomain: {
            type: "day",
            width: 10,
            height: 10,
            color: "#ededed",
        },
        scale: {
            color: {
                scheme: 'Greens',
                type: 'linear',
                domain: [0, 10, 20, 35, 55, 80],
            },
        }
    });
};

var setupCalendarControls = function() {
    $('#id-heatmap-next').on('click', () => {
        calHeatMapInstance.next();
    })
    $('#id-heatmap-previous').on('click', () => {
        calHeatMapInstance.previous();
    })

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
    $("[name=clearbiblequeue]").click(function(ev) {
        if (!confirm($('#id-i18n-dashboard-remove-verses-from-queue-confirm').text())) {
            ev.preventDefault();
        }
    });
    $("[name=clearcatechismqueue]").click(function(ev) {
        if (!confirm($('#id-i18n-dashboard-remove-catechism-from-queue-confirm').text())) {
            ev.preventDefault();
        }
    });
    $("[name=cancelpassage]").click(function(ev) {
        if (!confirm($('#id-i18n-dashboard-cancel-passage-confirm').text())) {
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

    var accountNode = document.getElementById('id-account-data');
    var accountName = accountNode == null ? "" : accountNode.attributes['data-username'].value;
    if (getSavedCalls(accountName).length > 0) {
        $("#id-unfinished-session-warning").show();
        $("#id-unfinished-session-unsaved-data-warning").show();
    }
};

$(document).ready(function() {
    setupDashboardControls();
});
