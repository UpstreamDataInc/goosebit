function secondsToRecentDate(t) {
  if (t == null) {
    return null;
  }
  t = Number(t);
  const d = Math.floor(t / 86400);
  const h = Math.floor((t % 86400) / 3600);
  const m = Math.floor(((t % 86400) % 3600) / 60);
  const s = Math.floor(((t % 86400) % 3600) % 60);

  if (d > 0) {
    return d + (d === 1 ? " day" : " days");
  } else if (h > 0) {
    return h + (h === 1 ? " hour" : " hours");
  } else if (m > 0) {
    return m + (m === 1 ? " minute" : " minutes");
  } else {
    return s + (s === 1 ? " second" : " seconds");
  }
}

async function updateFirmwareSelection(addSpecialMode = false) {
  try {
    const response = await fetch("/api/firmware/all");
    if (!response.ok) {
      console.error("Retrieving firmwares failed.");
      return;
    }
    const data = await response.json();
    const selectElem = document.getElementById("selected-fw");

    if (addSpecialMode) {
      let optionElem = document.createElement("option");
      optionElem.value = "rollout";
      optionElem.textContent = "rollout";
      selectElem.appendChild(optionElem);

      optionElem = document.createElement("option");
      optionElem.value = "latest";
      optionElem.textContent = "latest";
      selectElem.appendChild(optionElem);
    }

    data.forEach((item) => {
      const optionElem = document.createElement("option");
      optionElem.value = item["id"];
      optionElem.textContent = item["name"];
      selectElem.appendChild(optionElem);
    });
  } catch (error) {
    console.error("Failed to fetch device data:", error);
  }
}

async function post(url, object) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(object),
  });

  if (!response.ok) {
    throw new Error(`POST ${url} failed for ${JSON.stringify(object)}`);
  }
}
