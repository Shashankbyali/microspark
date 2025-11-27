// Tab switching
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const forms = document.querySelectorAll('.auth-form');
    
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            
            // Update active tab
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update active form
            forms.forEach(f => f.classList.remove('active'));
            document.getElementById(`${tab}-form`).classList.add('active');
            
            // Clear errors
            document.querySelectorAll('.error-message').forEach(e => {
                e.classList.remove('show');
                e.textContent = '';
            });
        });
    });
    
    // Sign in form
    document.getElementById('signinForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const errorDiv = document.getElementById('signin-error');
        errorDiv.classList.remove('show');
        
        const username = document.getElementById('signin-username').value;
        const password = document.getElementById('signin-password').value;
        
        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);
            
            const response = await fetch('/signin', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                window.location.href = data.redirect;
            } else {
                errorDiv.textContent = data.error || 'Sign in failed';
                errorDiv.classList.add('show');
            }
        } catch (error) {
            errorDiv.textContent = 'An error occurred. Please try again.';
            errorDiv.classList.add('show');
        }
    });
    
    // Sign up form
    document.getElementById('signupForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const errorDiv = document.getElementById('signup-error');
        errorDiv.classList.remove('show');
        
        const username = document.getElementById('signup-username').value;
        const email = document.getElementById('signup-email').value;
        const password = document.getElementById('signup-password').value;
        
        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('email', email);
            formData.append('password', password);
            
            const response = await fetch('/signup', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                window.location.href = data.redirect;
            } else {
                errorDiv.textContent = data.error || 'Sign up failed';
                errorDiv.classList.add('show');
            }
        } catch (error) {
            errorDiv.textContent = 'An error occurred. Please try again.';
            errorDiv.classList.add('show');
        }
    });
});

