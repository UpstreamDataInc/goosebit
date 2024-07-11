const CHUNK_SIZE = 10 * 1024 * 1024; // 10 MB chunk size
const form = document.getElementById('upload-form');
const fileInput = document.getElementById('file-upload');
const fileSubmit = document.getElementById('file-upload-submit');
const progressBar = document.getElementById('upload-progress');

form.addEventListener('submit', e => {
    e.preventDefault();
    sendFileChunks(fileInput.files[0])
});

const sendFileChunks = async (file) => {
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
    let start = 0;
    let uploadedChunks = 0;

    fileSubmit.disabled = true
    fileInput.disabled = true

    for (let i = 0; i < totalChunks; i++) {
        const end = Math.min(start + CHUNK_SIZE, file.size);
        const chunk = file.slice(start, end);
        const formData = new FormData();
        formData.append('chunk', chunk);
        formData.append('filename', file.name);
        if (i == 0) {
            formData.append('init', true);
        } else  {
            formData.append('init', false);
        }

        if (i == totalChunks - 1) {
            formData.append('done', true);
        } else {
            formData.append('done', false);
        }

        const response = await fetch("/ui/upload", {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            uploadedChunks++;
            const progress = (uploadedChunks / totalChunks) * 100;
            progressBar.style.width = `${progress}%`;
            progressBar.innerHTML = `${Math.round(progress)}%`;
        } else {
            if (response.status === 400) {
                result = await response.json()
                alerts = document.getElementById("upload-alerts");
                alerts.innerHTML = `<div class="alert alert-warning alert-dismissible fade show" role="alert">
                    ${result["detail"]}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>`
            }
        }

        start = end;
    }

    window.setTimeout(function () {
        resetProgress()
    }, 1000)
};

function resetProgress() {
    fileInput.disabled = false;
    fileSubmit.disabled = false;
    progressBar.style.width = `0%`;
    progressBar.innerHTML = `0%`;
    updateFirmwareList();
}

document.addEventListener("DOMContentLoaded", function() {
    updateFirmwareList();
});


function updateFirmwareList() {
    const url = '/api/firmware/all';

    fetch(url)
    .then(response => {
        if (!response.ok) {
            throw new Error('Request failed');
        }
        return response.json();
    })
    .then(data => {
        const list = document.getElementById('firmware-list');
        list.innerHTML = "";

        data.forEach(item => {
            const listItem = document.createElement('li');
            listItem.textContent = `${item["name"]}, size: ${(item["size"] / 1024 / 1024).toFixed(2)} MB`;
            listItem.classList = ["list-group-item d-flex justify-content-between align-items-center"];

            const btnGroup = document.createElement("div")
            btnGroup.classList = "btn-group"
            btnGroup.role = "group"

            const deleteBtn = document.createElement('button');
            deleteBtn.innerHTML =  "<i class='bi bi-trash'></i>";
            deleteBtn.classList = ["btn btn-danger"];
            deleteBtn.onclick = function() {deleteFirmware(item["name"])};

            const downloadBtn = document.createElement('button');
            downloadBtn.innerHTML = "<i class='bi bi-cloud-download'></i>";
            downloadBtn.classList = ["btn btn-primary"];
            downloadBtn.onclick = function() {window.location.href = `/api/download/${item["name"]}`};

            btnGroup.appendChild(deleteBtn);
            btnGroup.appendChild(downloadBtn);

            listItem.appendChild(btnGroup);
            list.appendChild(listItem);
        });
    })
    .catch(error => {
        console.error('Failed to fetch firmware data:', error);
    });
}

function deleteFirmware(file) {
    fetch('/api/firmware/delete', {
        method: 'POST',
        body: file,
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to delete firmware.');
        }
        updateFirmwareList();
        return response.json();
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
