document.addEventListener("DOMContentLoaded", function() {
    var logs_ws = create_ws(`/realtime/logs/${device}`);

    logs_ws.addEventListener('message', (event) => {
        res = JSON.parse(event.data);

        const logElem = document.getElementById('device-log');
        if (res["clear"]) {
            logElem.textContent = ""
        }
        logElem.textContent += res["log"];

        const progressElem = document.getElementById('install-progress');
        progressElem.style.width = `${res.progress}%`;
        progressElem.innerHTML = `${res.progress}%`;
    });
});

function create_ws(s) {
    var l = window.location;
    return new WebSocket(((l.protocol === "https:") ? "wss://" : "ws://") + l.hostname + (((l.port != 80) && (l.port != 443)) ? ":" + l.port : "") + s);
}
