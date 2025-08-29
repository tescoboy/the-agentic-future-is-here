// Buyer form functionality

document.addEventListener('DOMContentLoaded', function() {
    const briefForm = document.getElementById('briefForm');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const submitBtn = document.getElementById('submitBtn');
    
    if (briefForm) {
        briefForm.addEventListener('submit', function() {
            // Show loading overlay
            if (loadingOverlay) {
                loadingOverlay.classList.remove('d-none');
            }
            
            // Disable submit button
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i>Processing...';
            }
        });
    }
});

