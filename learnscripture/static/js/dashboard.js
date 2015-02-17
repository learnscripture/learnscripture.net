/*jslint browser: true, vars: true, plusplus: true */
/*globals $, jQuery, alert, confirm */
var learnscripture =
    (function (learnscripture, $) {
        "use strict";

        var setupCalendarHeatmap = function () {
            var cal = new CalHeatMap();
            var today = new Date();
            var year = today.getFullYear();
            var month = today.getMonth();
            var numberOfMonths = 8;
            month = month - (numberOfMonths - 1);
            if (month < 0) {
                month += 12;
                year -= 1;
            }
	        cal.init({
                cellSize: 10,
                data: $("#id-dashboard-script-data").attr('data-user-stats-verses-timeline-stats-csv-url'),
                dataType: "csv",
                displayLegend: false,
                domain: "month",
                domainLabelFormat: "%b %Y",
                itemSelector: '#id-heatmap-div',
                maxDate: today,
                nextSelector: '#id-heatmap-next',
                previousSelector: '#id-heatmap-previous',
                range: numberOfMonths,
                start: new Date(year, month, 1),
                subdomain: "x_day",
                afterLoadData: function(data) {
                    var stats = {};
                    for (var i = 0; i < data.length; i++) {
                        var ts = Date.parse(data[i]['Date']) / 1000;
                        var num = parseInt(data[i]['Verses started'], 10) + parseInt(data[i]['Verses tested'], 10);
                        stats[ts] = num;
                    }
                    return stats;
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
                if (!confirm("This will cancel learning this passage. " +
                             "Any test scores will be saved. " +
                             "Continue?")) {
                    ev.preventDefault();
                }
            });
            setupCalendarHeatmap();
        };

        learnscripture.setupDashboardControls = setupDashboardControls;
        return learnscripture;
    }(learnscripture || {}, $));

$(document).ready(function () {
    learnscripture.setupDashboardControls();
});
