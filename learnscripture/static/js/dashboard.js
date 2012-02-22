var learnscripture =
    (function(learnscripture, $) {

        var confirmClearQueue = function() {

        };

        var setupDashboardControls = function() {
            if (document.location.pathname.match(/\/dashboard/) == null) {
                return;
            }
            $("input[name=clearqueue]").click(function(ev) {
                if (!confirm("This will remove chosen verses from your queue " +
                            "for learning. To learn them you will have to " +
                            "select the verses or verse sets again. " +
                             "Continue?")) {
                    ev.preventDefault();
                }
            });
            $("input[name=cancelpassage]").click(function(ev) {
                if (!confirm("This will cancel learning this passage. " +
                             "Any test scores will be saved. " +
                             "Continue?")) {
                    ev.preventDefault();
                }
            });

        }

        learnscripture.setupDashboardControls = setupDashboardControls;
        return learnscripture;
    })(learnscripture || {}, $);

$(document).ready(function() {
    learnscripture.setupDashboardControls();
});