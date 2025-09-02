// Buyer form functionality

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Buyer.js loaded');
    const briefForm = document.getElementById('briefForm');
    const submitBtn = document.getElementById('submitBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    console.log('📋 Form found:', !!briefForm);
    console.log('🔘 Submit button found:', !!submitBtn);
    console.log('⏳ Loading overlay found:', !!loadingOverlay);
    
    if (briefForm) {
        briefForm.addEventListener('submit', function(e) {
            console.log('📤 Form submitted - showing loading overlay');
            
            // Show loading overlay using Bootstrap classes
            if (loadingOverlay) {
                loadingOverlay.classList.remove('d-none');
                loadingOverlay.classList.add('d-flex');
                console.log('✅ Loading overlay should now be visible');
            }
            
            // Disable submit button
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin me-2"></i>Processing...';
                console.log('✅ Submit button disabled');
            }
        });
    }
});

