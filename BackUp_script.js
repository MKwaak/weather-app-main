const ddlUnits = document.querySelector("#ddlUnits");
const divCityCountry = document.querySelector("#divCityCountry");
const divCurrentDate = document.querySelector("#divCurrentDate");
const divCurrentTemp = document.querySelector("#divCurrentTemp");
const searchForm = document.querySelector(".hero__search");
const searchInput = document.querySelector("#search");

let cityName, countryName;

ddlUnits.addEventListener("change", () => {
  getGeoData();
});

async function getGeoData() {
  async function getGeoData(search) {
    if (!search) return;

    const url = `https://nominatim.openstreetmap.org/search?q=${search}&format=jsonv2&addressdetails=1`;
  }

  const searchForm = document.querySelector(".hero__search");
  const searchInput = document.querySelector("#search");

  searchForm.addEventListener("submit", (e) => {
    e.preventDefault(); // prevent page reload
    const city = searchInput.value.trim();
    if (city) getGeoData(city);
  });

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    const result = await response.json();

    const { lat, lon } = result[0];
    loadlocationData(result);
    getWeatherData(lat, lon);
  } catch (error) {
    console.error(error.message);
  }
}

function loadlocationData(locationData) {
  const location = locationData[0].address;

  cityName =
    location.city || location.town || location.village || location.state;
  countryName = location.country_code.toUpperCase();

  const date = new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    weekday: "long",
  }).format(new Date());

  divCityCountry.textContent = `${cityName}, ${countryName}`;
  divCurrentDate.textContent = date;
}

async function getWeatherData(lat, lon) {
  let tempUnit = "celsius";
  let windUnit = "kmh";
  let precipUnit = "mm";
  let unitSymbol = "°C"; // for display

  if (ddlUnits.value === "F") {
    tempUnit = "fahrenheit";
    windUnit = "mph";
    precipUnit = "inch";
    unitSymbol = "°F";
  }

  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&daily=weather_code,temperature_2m_max,temperature_2m_min&hourly=temperature_2m,weather_code&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&wind_speed_unit=${windUnit}&temperature_unit=${tempUnit}&precipitation_unit=${precipUnit}`;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    const result = await response.json();
    console.log(result);

    // Current weather
    const current = result.current_weather;

    divCurrentTemp.innerHTML = `<span>${Math.round(current.temperature)}</span>${unitSymbol}`;
    document.getElementById("feels-like").textContent =
      `${Math.round(current.apparent_temperature || current.temperature)}${unitSymbol}`;
    document.getElementById("wind").textContent =
      `${Math.round(current.wind_speed)} ${windUnit}`;
    document.getElementById("humidity").textContent =
      `${current.relative_humidity ?? 0}%`;
    document.getElementById("precipitation").textContent =
      `${current.precipitation ?? 0} ${precipUnit}`;

    // TODO: update daily forecast
    // TODO: update hourly forecast
  } catch (error) {
    console.error(error.message);
  }
}

getGeoData();
