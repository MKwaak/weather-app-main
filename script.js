const ddlUnits = document.querySelector("#ddlUnits");
const divCityCountry = document.querySelector("#divCityCountry");
const divCurrentDate = document.querySelector("#divCurrentDate");
const divCurrentTemp = document.querySelector("#divCurrentTemp");
const searchForm = document.querySelector(".hero__search");
const searchInput = document.querySelector("#search");

// Global variables
let currentLat, currentLon;

// Load weather for a city
async function getGeoData(search) {
  if (!search) return;

  const url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(
    search,
  )}&format=jsonv2&addressdetails=1`;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Response status: ${response.status}`);

    const result = await response.json();
    if (!result[0]) throw new Error("City not found");

    const { lat, lon } = result[0];
    currentLat = lat;
    currentLon = lon;

    loadLocationData(result);
    getWeatherData(lat, lon);
  } catch (error) {
    console.error(error.message);
    alert("City not found. Please try again.");
  }
}

// Update city, country, date
function loadLocationData(locationData) {
  const location = locationData[0].address;
  const city =
    location.city || location.town || location.village || location.state;
  const country = location.country_code.toUpperCase();

  const date = new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    weekday: "long",
  }).format(new Date());

  divCityCountry.textContent = `${city}, ${country}`;
  divCurrentDate.textContent = date;
}

// Load weather data
async function getWeatherData(lat, lon) {
  // Determine units
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

  // Fetch weather data
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&hourly=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min&temperature_unit=${tempUnit}&wind_speed_unit=${windUnit}&precipitation_unit=${precipUnit}`;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Response status: ${response.status}`);

    const result = await response.json();
    console.log(result);

    // Current weather
    const current = result.current_weather;

    // Fallback to hourly arrays if values are missing
    const temp = current.temperature ?? result.hourly?.temperature_2m?.[0] ?? 0;
    const feelsLike = result.hourly?.apparent_temperature?.[0] ?? temp;
    const windSpeed =
      current.wind_speed ?? result.hourly?.wind_speed_10m?.[0] ?? 0;
    const humidity = result.hourly?.relative_humidity_2m?.[0] ?? 0;
    const precipitation = result.hourly?.precipitation?.[0] ?? 0;

    // Update DOM
    divCurrentTemp.innerHTML = `<span>${Math.round(temp)}</span>${unitSymbol}`;
    document.getElementById("feels-like").textContent =
      `${Math.round(feelsLike)}${unitSymbol}`;
    document.getElementById("wind").textContent =
      `${Math.round(windSpeed)} ${windUnit}`;
    document.getElementById("humidity").textContent =
      `${Math.round(humidity)}%`;
    document.getElementById("precipitation").textContent =
      `${Math.round(precipitation)} ${precipUnit}`;

    // TODO: update daily and hourly forecast dynamically
  } catch (error) {
    console.error(error.message);
  }
}

// Event listeners
searchForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const city = searchInput.value.trim();
  if (city) getGeoData(city);
});

ddlUnits.addEventListener("change", () => {
  if (currentLat && currentLon) {
    getWeatherData(currentLat, currentLon);
  }
});

// Initial load (optional: default city)
getGeoData("los angeles, ca");
