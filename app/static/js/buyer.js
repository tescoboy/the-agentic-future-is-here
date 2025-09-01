// Buyer form functionality

document.addEventListener('DOMContentLoaded', function() {
    const briefForm = document.getElementById('briefForm');
    const submitBtn = document.getElementById('submitBtn');
    
    if (briefForm) {
        briefForm.addEventListener('submit', function(e) {
            // Show loading overlay
            const loadingOverlay = document.getElementById('loadingOverlay');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'flex';
            }
            
            // Disable submit button
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i>Processing...';
            }
        });
    }
});

