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
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&hourly=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,wind_speed_10m&daily=temperature_2m_max,temperature_2m_min,weather_code&temperature_unit=${tempUnit}&wind_speed_unit=${windUnit}&precipitation_unit=${precipUnit}&timezone=auto`;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Response status: ${response.status}`);

    const result = await response.json();
    console.log(result.daily.weather_code);

    //console.log("Local date:", new Date().toDateString());
    //console.log("Daily[0]:", result.daily.time[0]);

    // Current weather
    const current = result.current_weather;
    const temp = current.temperature ?? 0;
    const windSpeed = current.wind_speed ?? 0;

    const feelsLike = result.hourly.apparent_temperature?.[0] ?? temp;
    const humidity = result.hourly.relative_humidity_2m?.[0] ?? 0;
    const precipitation = result.hourly.precipitation?.[0] ?? 0;

    // Update DOM "DOM = Document Object Model, a tree of objects that javascript can read"
    divCurrentTemp.innerHTML = `<span>${Math.round(temp)}</span>${unitSymbol}`;
    document.getElementById("feels-like").textContent =
      `${Math.round(feelsLike)}${unitSymbol}`;
    document.getElementById("wind").textContent =
      `${Math.round(windSpeed)} ${windUnit}`;
    document.getElementById("humidity").textContent =
      `${Math.round(humidity)}%`;
    document.getElementById("precipitation").textContent =
      `${Math.round(precipitation)} ${precipUnit}`;

    // Step 1: pass current weather to daily forecast
    console.log("before renderDailyForecast");
    renderDailyForecast(result.daily, unitSymbol, current);
    console.log("after renderDailyForecast");

    // TODO: update daily and hourly forecast dynamically
    //renderDailyForecast(result.daily, unitSymbol);
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

function renderDailyForecast(daily, unitSymbol, currentWeather) {
  const dailyContainer = document.getElementById("dailyForecast");

  console.log("daily container:", dailyContainer);

  dailyContainer.innerHTML = ""; // clear old data

  daily.time.forEach((dateString, index) => {
    if (index > 6) return; // limit to 7 days

    // Determine the day name
    const date = index === 0 ? new Date() : new Date(dateString);
    const dayName = date.toLocaleDateString("en-US", { weekday: "short" });

    // Determine the icon file
    const iconFile =
      index === 0
        ? getWeatherIconName(currentWeather.weathercode)
        : getWeatherIconName(daily.weather_code[index]);

    // Log for debugging
    console.log(index, dayName, "icon:", iconFile);

    // --- Create the HTML ---
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
        <img
            class="daily__day-icon"
            src="/assets/images/${iconFile}"
            alt=""
            aria-hidden="true"
        />
        <div class="daily__day-temps">
            <span class="daily__day-high">${maxTemp}${unitSymbol}</span>
            <span class="daily__day-low">${minTemp}${unitSymbol}</span>
        </div>
    `;

    dailyContainer.appendChild(dayEl);
  });
}

function loadCurrentWeather(weather) {}

function LoadDailyForecast(weather) {
  let daily = weather.daily;

  for (let i = 0; i < 7; i++) {
    let date = new Date(daily.time[i]).getDay();
    console.log(
      new Intl.DateTimeFormat("en-US", { weekday: "long" }).format(date),
    );
    //console.log(day); = to test day
  }
}

// WHEN we get weatherCode <51> THEN it returns 'drizzle'
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

  let fileName = `icon-${weatherCodes[code]}.webp`;

  return fileName;
}

// Initial load (optional: default city)
getGeoData("Rotterdam");

//console.log(getWeatherIconName(0));
