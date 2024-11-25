document.addEventListener("DOMContentLoaded", async () => {
    const res = await get_request(`/ui/bff/devices/${device}/log`);

    const logElem = document.getElementById("device-log");
    logElem.textContent = res.log;

    const progressElem = document.getElementById("install-progress");
    progressElem.style.width = `${res.progress}%`;
    progressElem.innerHTML = `${res.progress}%`;
});
