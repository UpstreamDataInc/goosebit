const loginForm = document.getElementById("login_form");
const errorContainer = document.getElementById("login_error");

async function login() {
    const formData = new FormData(loginForm);

    try {
        const response = await fetch("/login", {
            method: "POST",
            body: formData,
        });

        if (response.status === 401) {
            const result = await response.json();
            errorContainer.textContent = result.detail || "Failed to login.";
            errorContainer.classList.remove("d-none");
            return;
        }

        if (!response.ok) {
            errorContainer.textContent = "Something went wrong. Please try again.";
            errorContainer.classList.remove("d-none");
            return;
        }

        const tokenData = await response.json();
        document.cookie = `session_id=${tokenData.access_token}; path=/`;
        location.reload();
    } catch (error) {
        errorContainer.textContent = "Network error. Please try again.";
        errorContainer.classList.remove("d-none");
    }
}

loginForm.addEventListener("submit", (event) => {
    event.preventDefault();
    errorContainer.classList.add("d-none"); // Hide error before new attempt
    login();
});
