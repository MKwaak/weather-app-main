const ddlUnits = document.querySelector("#ddlUnits");
const divCityCountry = document.querySelector("#divCityCountry");
const divCurrentDate = document.querySelector("#divCurrentDate");
const divCurrentTemp = document.querySelector("#divCurrentTemp");
const searchForm = document.querySelector(".hero__search");
const searchInput = document.querySelector("#search");

// --- 1. LOSSE LOGISCHE FUNCTIES (TESTBAAR) ---
const priorityCountryCodes = [
  "gr",
  "nl",
  "de",
  "fr",
  "gb",
  "es",
  "it",
  "no",
  "be",
  "at",
];

function selectLocation(result) {
  if (!result || result.length === 0) return null;
  const euSelected = result.find(
    (r) =>
      r.address &&
      r.address.country_code &&
      priorityCountryCodes.includes(r.address.country_code.toLowerCase()),
  );
  return euSelected || result[0];
}

function getCityName(address) {
  if (!address) return "Unknown location";
  return (
    address.city ||
    address.town ||
    address.village ||
    address.municipality ||
    address.suburb ||
    address.city_district ||
    address.county ||
    address.state_district ||
    address.state ||
    address.province ||
    address.region ||
    "Unknown location"
  );
}

function getWeatherIconName(code) {
  const weatherCodes = {
    0: "sunny",
    1: "partly-cloudy",
    2: "partly-cloudy",
    3: "overcast",
    45: "fog",
    48: "fog",
    51: "drizzle",
    53: "drizzle",
    55: "drizzle",
    56: "drizzle",
    57: "drizzle",
    61: "rain",
    63: "rain",
    65: "rain",
    66: "rain",
    67: "rain",
    80: "rain",
    81: "rain",
    82: "rain",
    71: "snow",
    73: "snow",
    75: "snow",
    77: "snow",
    85: "snow",
    86: "snow",
    95: "storm",
    96: "storm",
    99: "storm",
  };
  const icon = weatherCodes[code] ?? "overcast";
  return `icon-${icon}.webp`;
}

// --- 2. GLOBAL VARIABLES & ASYNC LOGIC ---
let currentLat, currentLon;

async function getGeoData(search) {
  if (!search) return;

  const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(
    search,
  )}&format=jsonv2&addressdetails=1`;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Response status: ${response.status}`);

    const result = await response.json();
    if (!result || result.length === 0) throw new Error("City not found");

    // Gebruik de testbare selectie-logica
    const selected = selectLocation(result);

    if (!selected || !selected.lat || !selected.lon) {
      currentLat = 51.9244; // Rotterdam default
      currentLon = 4.4777;
    } else {
      currentLat = selected.lat;
      currentLon = selected.lon;
    }

    loadLocationData(result, selected);
    getWeatherData(currentLat, currentLon);
  } catch (error) {
    console.error(error.message);
    alert("City not found. Please try again.");
  }
}

function loadLocationData(locationData, selectedResult = null) {
  const address = selectedResult
    ? selectedResult.address
    : locationData[0].address;
  const city = getCityName(address);
  const country = address.country_code
    ? address.country_code.toUpperCase()
    : "??";

  const date = new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    weekday: "long",
  }).format(new Date());

  divCityCountry.textContent = `${city}, ${country}`;
  divCurrentDate.textContent = date;
}

async function getWeatherData(lat, lon) {
  let tempUnit = "celsius";
  let windUnit = "kmh";
  let precipUnit = "mm";
  let unitSymbol = "°C";

  if (ddlUnits.value === "F") {
    tempUnit = "fahrenheit";
    windUnit = "mph";
    precipUnit = "inch";
    unitSymbol = "°F";
  }

  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&hourly=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,wind_speed_10m,weather_code&daily=temperature_2m_max,temperature_2m_min,weather_code&temperature_unit=${tempUnit}&wind_speed_unit=${windUnit}&precipitation_unit=${precipUnit}&timezone=auto`;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Response status: ${response.status}`);
    const result = await response.json();

    if (!result.daily || !result.hourly) return;

    const current = result.current_weather;
    const temp = current.temperature;
    const windSpeed = current.windspeed;

    divCurrentTemp.innerHTML = `<span>${Math.round(temp)}</span>${unitSymbol}`;

    const currentIconImg = document.querySelector(
      ".current__weather .current__icon",
    );
    if (currentIconImg) {
      currentIconImg.src = `/assets/images/${getWeatherIconName(current.weathercode)}`;
    }

    document.getElementById("feels-like").textContent =
      `${Math.round(result.hourly.apparent_temperature[0])}${unitSymbol}`;
    document.getElementById("wind").textContent =
      `${Math.round(windSpeed)} ${windUnit}`;
    document.getElementById("humidity").textContent =
      `${result.hourly.relative_humidity_2m[0]}%`;
    document.getElementById("precipitation").textContent =
      `${result.hourly.precipitation[0]} ${precipUnit}`;

    renderDailyForecast(result.daily, unitSymbol, current);
    renderHourlyForecast(result, unitSymbol);
  } catch (error) {
    console.error("Weather error:", error);
  }
}

// --- 3. RENDERING & EVENTS ---
function renderDailyForecast(daily, unitSymbol, currentWeather) {
  const dailyContainer = document.getElementById("dailyForecast");
  dailyContainer.innerHTML = "";

  daily.time.forEach((dateString, index) => {
    if (index > 6) return;
    const date = index === 0 ? new Date() : new Date(dateString);
    const dayName = date.toLocaleDateString("en-US", { weekday: "short" });
    const iconFile =
      index === 0
        ? getWeatherIconName(currentWeather.weathercode)
        : getWeatherIconName(daily.weather_code[index]);
    const maxTemp =
      index === 0
        ? Math.round(currentWeather.temperature)
        : Math.round(daily.temperature_2m_max[index]);
    const minTemp =
      index === 0
        ? Math.round(currentWeather.temperature)
        : Math.round(daily.temperature_2m_min[index]);

    const dayEl = document.createElement("div");
    dayEl.className = "daily__day block";
    dayEl.innerHTML = `
        <div class="daily__day-title">${dayName}</div>
        <img class="daily__day-icon" src="/assets/images/${iconFile}" alt="" />
        <div class="daily__day-temps">
            <span class="daily__day-high">${maxTemp}${unitSymbol}</span>
            <span class="daily__day-low">${minTemp}${unitSymbol}</span>
        </div>`;
    dailyContainer.appendChild(dayEl);
  });
}

function renderHourlyForecast(result, unitSymbol) {
  const hourlyContainer = document.getElementById("hourlyForecast");
  const hourlyDaySelect = document.getElementById("hourlyDay");
  hourlyContainer.innerHTML = "";
  hourlyDaySelect.innerHTML = "";

  const now = new Date(result.current_weather.time);
  let startIndex = result.hourly.time.findIndex((t) => new Date(t) >= now) || 0;

  const weekdayName = new Date(
    result.hourly.time[startIndex],
  ).toLocaleDateString("en-US", { weekday: "long" });
  const option = document.createElement("option");
  option.textContent = weekdayName;
  hourlyDaySelect.appendChild(option);

  for (let i = startIndex; i < startIndex + 8; i++) {
    if (!result.hourly.time[i]) break;
    const time = new Date(result.hourly.time[i]);
    const formattedHour = time.getHours() % 12 || 12;
    const ampm = time.getHours() >= 12 ? "PM" : "AM";
    const iconFile = getWeatherIconName(result.hourly.weather_code[i]);

    const hourEl = document.createElement("div");
    hourEl.className = "hourly__hour";
    if (time.getHours() === now.getHours()) hourEl.classList.add("current");

    hourEl.innerHTML = `
            <img class="hourly__hour-icon" src="/assets/images/${iconFile}" alt="" />
            <p class="hourly__hour-time">${formattedHour}:00 ${ampm}</p>
            <p class="hourly__hour-temp">${Math.round(result.hourly.temperature_2m[i])}${unitSymbol}</p>`;
    hourlyContainer.appendChild(hourEl);
  }
}

searchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const city = searchInput.value.trim();
  if (city) getGeoData(city);
});

ddlUnits.addEventListener("change", () => {
  if (currentLat && currentLon) getWeatherData(currentLat, currentLon);
});

// Initial load
getGeoData("Rotterdam");

// --- 4. EXPORTS VOOR JEST ---
if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    priorityCountryCodes,
    selectLocation,
    getCityName,
    getWeatherIconName,
  };
}
