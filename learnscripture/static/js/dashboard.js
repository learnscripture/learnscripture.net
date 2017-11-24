/*jslint browser: true, vars: true, plusplus: true */
/*globals alert, confirm */
"use strict";

require('cal-heatmap/cal-heatmap.css');

var $ = require('jquery');
var CalHeatMap = require('cal-heatmap');

var setupCalendarHeatmap = function () {
    if ($('#id-heatmap-div').length == 0) {
        return;
    }
    var cal = new CalHeatMap();
    var today = new Date();
    var year = today.getFullYear();
    var month = today.getMonth();
    // Go back 2 years, and then clip the left hand side
    // This gives the best results visually.
    var numberOfYears = 2;
    year -= numberOfYears;
	cal.init({
        cellSize: 10, // need to change #id-heatmap-div height if this is changed.
        data: $("#id-dashboard-script-data").attr('data-user-stats-verses-timeline-stats-csv-url') + "?r=" + Math.floor(Math.random() * 1000000000).toString(),
        dataType: "csv",
        displayLegend: false,
        domain: "month",
        domainLabelFormat: "%b %Y",
        itemSelector: '#id-heatmap-div',
        maxDate: today,
        nextSelector: '#id-heatmap-next',
        previousSelector: '#id-heatmap-previous',
        range: numberOfYears * 12 + 1,
        start: new Date(year, month, 1),
        subDomainDateFormat: "%Y-%m-%d",
        legend: [1,10,20,35,50,65],
        highlight: "now",
        afterLoadData: function(data) {
            // calculate dict in form required by CalHeatMap. Also
            // calculate streaks, relying on fact that data has zeros in
            // it and is sorted correctly.
            var stats = {};
            var biggestStreak = 0;
            var currentStreak = 0;
            for (var i = 0; i < data.length; i++) {
                var ts = Date.parse(data[i]['Date']) / 1000;
                var num = parseInt(data[i]['Verses started'], 10) + parseInt(data[i]['Verses tested'], 10);
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
            $('#id-heatmap-loading').remove();
            $('#id-current-streak').text(currentStreak.toString() + " " + (currentStreak == 1 ? "day" : "days"));
            $('#id-biggest-streak').text(biggestStreak.toString() + " " + (biggestStreak == 1 ? "day" : "days"));
            return stats;
        }
    });
    $('#id-heatmap-div').on('click', 'svg rect', function (ev) {
        var candidates = ev.currentTarget.parentNode.childNodes;
        for (var i = 0; i < candidates.length; i++) {
            var node = candidates[i];
            if (node.tagName == 'title') {
                $('#id-heatmap-domain-title').text(node.textContent);
            }
        }
    });
};

var setupDashboardControls = function () {
    if (document.location.pathname.match(/\/dashboard/) === null) {
        return;
    }
    $("input[name=clearbiblequeue]").click(function (ev) {
        if (!confirm("This will remove chosen verses from your queue " +
                     "for learning. To learn them you will have to " +
                     "select the verses or verse sets again. " +
                     "Continue?")) {
            ev.preventDefault();
        }
    });
    $("input[name=clearcatechismqueue]").click(function (ev) {
        if (!confirm("This will remove chosen catechism questions from " +
                     "your queue for learning. To learn them you will have to " +
                     "select the catechism again. " +
                     "Continue?")) {
            ev.preventDefault();
        }
    });
    $("input[name=cancelpassage]").click(function (ev) {
        if (!confirm("This will cancel learning this passage in this version. " +
                     "Any test scores will be saved. " +
                     "Continue?")) {
            ev.preventDefault();
        }
    });
    setupCalendarHeatmap();
};

$(document).ready(function () {
    setupDashboardControls();
});
