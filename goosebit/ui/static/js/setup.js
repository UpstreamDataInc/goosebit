setupForm = document.getElementById("setup_form");

async function setup() {
    const formData = new FormData(setupForm);

    if (!(formData.password === formData.password_confirm)) {
        console.error("Passwords dont match");
        return;
    }

    try {
        const response = await fetch("/setup", {
            method: "POST",
            body: formData,
        });
        tokenData = await response.json();
        document.cookie = `session_id=${tokenData.access_token}; path=/`;
        window.location.assign("/");
    } catch (e) {
        // handle form errors later
        console.error(e);
    }
}

setupForm.addEventListener("submit", (event) => {
    event.preventDefault();
    setup();
});
