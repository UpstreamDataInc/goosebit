loginForm = document.getElementById("login_form");

async function login() {
    const formData = new FormData(loginForm);

    try {
        const response = await fetch("/login", {
            method: "POST",
            body: formData,
        });
        tokenData = await response.json();
        document.cookie = `session_id=${tokenData.access_token}; path=/`;
        location.reload();
    } catch (e) {
        // handle form errors later
        console.error(e);
    }
}

loginForm.addEventListener("submit", (event) => {
    event.preventDefault();
    login();
});
