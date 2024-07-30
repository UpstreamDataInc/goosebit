function secondsToRecentDate(t) {
  if (t == null) {
    return null;
  }
  t = Number(t);
  var d = Math.floor(t / 86400);
  var h = Math.floor((t % 86400) / 3600);
  var m = Math.floor(((t % 86400) % 3600) / 60);
  var s = Math.floor(((t % 86400) % 3600) % 60);

  if (d > 0) {
    return d + (d == 1 ? " day" : " days");
  } else if (h > 0) {
    return h + (h == 1 ? " hour" : " hours");
  } else if (m > 0) {
    return m + (m == 1 ? " minute" : " minutes");
  } else {
    return s + (s == 1 ? " second" : " seconds");
  }
}

function updateFirmwareSelection(addSpecialMode = false) {
  const url = "/api/firmware/all";

  fetch(url)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Request failed");
      }
      return response.json();
    })
    .then((data) => {
      selectElem = document.getElementById("selected-fw");

      if (addSpecialMode) {
        optionElem = document.createElement("option");
        optionElem.value = "rollout";
        optionElem.textContent = "rollout";
        selectElem.appendChild(optionElem);

        optionElem = document.createElement("option");
        optionElem.value = "latest";
        optionElem.textContent = "latest";
        selectElem.appendChild(optionElem);
      }

      data.forEach((item) => {
        optionElem = document.createElement("option");
        optionElem.value = item["id"];
        optionElem.textContent = item["name"];
        selectElem.appendChild(optionElem);
      });
    })
    .catch((error) => {
      console.error("Failed to fetch device data:", error);
    });
}
