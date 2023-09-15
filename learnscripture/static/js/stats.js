import "jquery.flot/jquery.flot";
import "jquery.flot/jquery.flot.time";
import "jquery.flot/jquery.flot.stack";

$(function() {
    var stats = JSON.parse($('#stats-json').attr('data-val'));
    $.plot("#id-verses-tested-graph",
        [
            {
                label: "Started",
                data: stats.verses_started
            },
            {
                label: "Tested",
                data: stats.verses_tested
            }
        ],
        {
            xaxis: {
                mode: "time",
                ticks: 10
            },
            yaxis: { min: 0 },
            legend: { position: "nw" },
            series: {
                lines: { show: true, fill: false },
            }

        });

    $.plot("#id-accounts-graph",
        [
            {
                label: "New accounts",
                data: stats.new_accounts,
                yaxis: 1
            },
            {
                label: "Active accounts",
                data: stats.active_accounts,
                yaxis: 2
            },
        ],
        {
            xaxis: {
                mode: "time",
                ticks: 10
            },
            yaxes: [{
                min: 0,
                position: 'left'
            },
            {
                min: 0,
                position: 'right'
            }],
            legend: { position: "nw" },
            series: {
                lines: { show: true, fill: false },
            }
        }
    );

});
