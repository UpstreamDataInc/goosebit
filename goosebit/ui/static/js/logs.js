document.addEventListener("DOMContentLoaded", () => {
    const logs_ws = create_ws(`/realtime/logs/${device}`);

    logs_ws.addEventListener("message", (event) => {
        const res = JSON.parse(event.data);

        const logElem = document.getElementById("device-log");
        if (res.clear) {
            logElem.textContent = "";
        }
        logElem.textContent += res.log;

        const progressElem = document.getElementById("install-progress");
        progressElem.style.width = `${res.progress}%`;
        progressElem.innerHTML = `${res.progress}%`;
    });
});

function create_ws(s) {
    const l = window.location;
    const protocol = l.protocol === "https:" ? "wss://" : "ws://";
    const port = l.port !== "80" || l.port !== "443" ? l.port : "";
    const url = `${protocol}${l.hostname}:${port}${s}`;
    return new WebSocket(url);
}
