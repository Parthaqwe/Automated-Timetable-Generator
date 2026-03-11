// Custom scripts for Automated Timetable Generator
document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 4 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            // Check if alert still exists and bootstrap is loaded
            if (document.body.contains(alert) && typeof bootstrap !== 'undefined') {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 4000);
    });
});
