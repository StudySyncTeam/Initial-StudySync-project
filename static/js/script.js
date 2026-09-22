document.addEventListener("DOMContentLoaded", () => {

    // Container & Button Controls (kept for compatibility with a
    // sliding-panel layout, if one is ever added back)
    const container = document.getElementById('container');
    const registerBtn = document.getElementById('register');
    const loginBtn = document.getElementById('login');

    if (registerBtn && container) {
        registerBtn.addEventListener('click', () => {
            container.classList.add("active");
        });
    }
    if (loginBtn && container) {
        loginBtn.addEventListener('click', () => {
            container.classList.remove("active");
        });
    }

    // Tab Switching Logic
    const tabSignin = document.getElementById('tab-signin');
    const tabSignup = document.getElementById('tab-signup');
    const formSignin = document.getElementById('form-signin');
    const formSignup = document.getElementById('form-signup');

    if (tabSignin && tabSignup) {
        tabSignin.addEventListener('click', () => {
            tabSignin.classList.add('active');
            tabSignup.classList.remove('active');
            if (formSignin) formSignin.classList.add('active');
            if (formSignup) formSignup.classList.remove('active');
        });

        tabSignup.addEventListener('click', () => {
            tabSignup.classList.add('active');
            tabSignin.classList.remove('active');
            if (formSignup) formSignup.classList.add('active');
            if (formSignin) formSignin.classList.remove('active');
        });
    }

    // 3D Tilt Effect on Hover
    const cards = document.querySelectorAll('.tilt-card, .bento-item');
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = ((y - centerY) / centerY) * -12;
            const rotateY = ((x - centerX) / centerX) * 12;
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(8px)`;
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)`;
        });
    });

    // NOTE: form-signin and form-signup are real <form> elements that POST
    // to Flask (action="{{ url_for('login') }}" / "{{ url_for('register') }}").
    // Do NOT intercept their submit event here — app.py already handles
    // validating the login/registration and redirects to /dashboard on
    // success. Adding a submit listener with e.preventDefault() would stop
    // the form from ever reaching the server.
});