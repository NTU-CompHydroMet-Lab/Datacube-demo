const state = {
  config: null,
  overlay: null,
  tileLayer: null,
  map: null,
};

const yearSelect = document.querySelector("#yearSelect");
const classList = document.querySelector("#classList");
const statsList = document.querySelector("#statsList");
const statusBox = document.querySelector("#status");

function setStatus(message, mode = "info") {
  statusBox.textContent = message;
  statusBox.dataset.mode = mode;
}

function selectedClasses() {
  return [...document.querySelectorAll("input[name='classCode']:checked")]
    .map((input) => input.value)
    .join(",");
}

function leafletBounds(bbox) {
  return [
    [bbox.south, bbox.west],
    [bbox.north, bbox.east],
  ];
}

function refreshMapSize() {
  if (!state.map) {
    return;
  }

  requestAnimationFrame(() => {
    state.map.invalidateSize({ pan: false });
  });
}

function renderClasses(classes) {
  classList.innerHTML = "";
  classes.forEach((item) => {
    const id = `class-${item.code}`;
    const row = document.createElement("label");
    row.className = "class-row";
    row.innerHTML = `
      <input id="${id}" name="classCode" type="checkbox" value="${item.code}" checked />
      <span class="swatch" style="background:${item.color}"></span>
      <span class="class-code">${item.code}</span>
      <span class="class-name">${item.name}</span>
    `;
    classList.appendChild(row);
  });

  classList.addEventListener("change", updateOverlay);
}

function renderYears(years) {
  yearSelect.innerHTML = "";
  years.forEach((year) => {
    const option = document.createElement("option");
    option.value = year;
    option.textContent = year;
    yearSelect.appendChild(option);
  });
  yearSelect.value = years[years.length - 1];
  yearSelect.addEventListener("change", updateOverlay);
}

function renderStats(stats) {
  statsList.innerHTML = "";
  stats
    .filter((row) => row.pixel_count > 0)
    .sort((a, b) => b.area_km2 - a.area_km2)
    .forEach((row) => {
      const item = document.createElement("div");
      item.className = "stat-row";
      item.innerHTML = `
        <span>${row.name}</span>
        <strong>${row.area_km2.toLocaleString(undefined, { maximumFractionDigits: 2 })} km2</strong>
      `;
      statsList.appendChild(item);
    });
}

async function updateOverlay() {
  const year = yearSelect.value;
  const classes = selectedClasses();
  const bounds = leafletBounds(state.config.bbox);
  const query = new URLSearchParams({ year, classes, t: Date.now().toString() });

  setStatus("Rendering overlay...");

  const nextOverlay = L.imageOverlay(`/api/overlay.png?${query.toString()}`, bounds, {
    opacity: 0.78,
    interactive: false,
  });

  nextOverlay.once("load", () => {
    if (state.overlay) {
      state.map.removeLayer(state.overlay);
    }
    state.overlay = nextOverlay;
    refreshMapSize();
  });

  nextOverlay.once("error", () => {
    setStatus("Overlay failed", "error");
  });

  nextOverlay.addTo(state.map);

  const response = await fetch(`/api/stats?${new URLSearchParams({ year, classes })}`);
  if (!response.ok) {
    setStatus("Stats failed", "error");
    return;
  }
  const payload = await response.json();
  renderStats(payload.stats);
  setStatus(`Showing ${year}`, "ready");
}

async function init() {
  const response = await fetch("/api/config");
  if (!response.ok) {
    setStatus("Config failed", "error");
    return;
  }

  state.config = await response.json();
  const bounds = leafletBounds(state.config.bbox);

  state.map = L.map("map", {
    zoomControl: false,
    preferCanvas: true,
  });

  L.control.zoom({ position: "bottomright" }).addTo(state.map);
  state.tileLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    keepBuffer: 4,
    updateWhenIdle: false,
    updateWhenZooming: false,
    crossOrigin: true,
    attribution: "&copy; OpenStreetMap contributors",
  });

  state.tileLayer.on("tileerror", () => {
    setStatus("Basemap tile failed", "error");
  });

  state.tileLayer.addTo(state.map);

  state.map.fitBounds(bounds);
  refreshMapSize();
  window.addEventListener("resize", refreshMapSize);
  setTimeout(refreshMapSize, 250);
  setTimeout(refreshMapSize, 750);

  renderYears(state.config.years);
  renderClasses(state.config.classes);
  await updateOverlay();
}

init().catch((error) => {
  console.error(error);
  setStatus("Application error", "error");
});
