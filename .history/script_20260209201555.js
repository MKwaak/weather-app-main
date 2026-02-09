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
    if (!result || result.length === 0) throw new Error("City not found");

    // 🔍 Debug: inspect all returned locations
    console.table(
      result.map((r) => ({
        display_name: r.display_name,
        country: r.address?.country ?? "(unknown)",
        country_code: r.address?.country_code ?? "(unknown)",
        state: r.address?.state ?? "(unknown)",
        city:
          r.address?.city ||
          r.address?.town ||
          r.address?.village ||
          r.address?.municipality ||
          "(unknown)",
        lat: r.lat,
        lon: r.lon,
      })),
    );

    // --- NIEUWE LOGICA: EU PRIORITEIT ---
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

    // Zoek of er een resultaat tussen zit dat in onze prioriteitslijst staat
    const euSelected = result.find(
      (r) =>
        r.address &&
        r.address.country_code &&
        priorityCountryCodes.includes(r.address.country_code.toLowerCase()),
    );

    // Als we een EU match hebben, pak die. Anders pakken we gewoon de allereerste uit de lijst.
    const selected = euSelected || result[0];
    // ------------------------------------

    if (!selected || !selected.lat || !selected.lon) {
      console.warn(
        "No valid coordinates returned, using default city (Rotterdam).",
      );
      currentLat = 51.9244; // Rotterdam
      currentLon = 4.4777;
    } else {
      currentLat = selected.lat;
      currentLon = selected.lon;
    }

    // 🔹 Load location and weather
    loadLocationData(result); // optional: show full list to user later
    getWeatherData(currentLat, currentLon);
  } catch (error) {
    console.error(error.message);
    alert("City not found. Please try again.");
  }
}

// Update city, country, date
function loadLocationData(locationData, selectedResult = null) {
  // Als we een specifiek geselecteerd resultaat hebben, gebruik die.
  // Anders vallen we terug op de eerste in de lijst.
  const address = selectedResult
    ? selectedResult.address
    : locationData[0].address;

  // 2. De "slimme zoektocht" naar de stadsnaam (deze was al goed!)
  const city =
    address.city ||
    address.town ||
    address.village ||
    address.municipality ||
    address.suburb ||
    address.city_district ||
    // NIEUW: Voor steden die ook een provincie/regio zijn (zoals Oslo, Berlijn of Wenen)
    address.county ||
    address.state_district ||
    address.state ||
    address.province ||
    address.region ||
    "Unknown location";

  // 3. FIX: Gebruik 'address' in plaats van 'location'
  console.log("Full address object:", address);

  // 4. FIX: landcode ophalen uit address (met een extra check voor de veiligheid)
  const country = address.country_code
    ? address.country_code.toUpperCase()
    : "??";

  const date = new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    weekday: "long",
  }).format(new Date());

  // 5. De tekst in de HTML zetten
  divCityCountry.textContent = `${city}, ${country}`;
  divCurrentDate.textContent = date;
}

// Load weather data
async function getWeatherData(lat, lon) {
  // 1️⃣ Units
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

  // 2️⃣ Build API URL
  const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&hourly=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,wind_speed_10m,weather_code&daily=temperature_2m_max,temperature_2m_min,weather_code&temperature_unit=${tempUnit}&wind_speed_unit=${windUnit}&precipitation_unit=${precipUnit}&timezone=auto`;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Response status: ${response.status}`);

    const result = await response.json();
    console.log("Weather API result:", result);

    if (!result.daily || !result.hourly) {
      console.warn("No daily/hourly data available");
      return;
    }

    // 3️⃣ Current weather (use API or fallback to closest hour)
    const current =
      result.current_weather ??
      (() => {
        const now = new Date();
        let closestIndex = 0;

        result.hourly.time.forEach((t, i) => {
          const diffNow = Math.abs(new Date(t) - now);
          const diffClosest = Math.abs(
            new Date(result.hourly.time[closestIndex]) - now,
          );
          if (diffNow < diffClosest) closestIndex = i;
        });

        return {
          temperature: result.hourly.temperature_2m[closestIndex],
          windspeed: result.hourly.wind_speed_10m[closestIndex], // ⚡ correct property
          weathercode: result.hourly.weather_code[closestIndex],
          time: result.hourly.time[closestIndex],
        };
      })();

    // 4️⃣ Extract current weather details safely
    const temp = current.temperature ?? 0;
    const windSpeed = current.windspeed ?? 0; // ⚡ now works
    const feelsLike = result.hourly.apparent_temperature?.[0] ?? temp;
    const humidity = result.hourly.relative_humidity_2m?.[0] ?? 0;
    const precipitation = result.hourly.precipitation?.[0] ?? 0;

    // 5️⃣ Update DOM
    divCurrentTemp.innerHTML = `<span>${Math.round(temp)}</span>${unitSymbol}`;
    // --- VOEG DIT HIER TOE ---
    const currentIconImg = document.querySelector(
      ".current__weather .current__icon",
    );
    if (currentIconImg) {
      const currentIconFile = getWeatherIconName(current.weathercode);
      currentIconImg.src = `/assets/images/${currentIconFile}`;
    }
    // --------------------------
    document.getElementById("feels-like").textContent =
      `${Math.round(feelsLike)}${unitSymbol}`;
    document.getElementById("wind").textContent =
      `${Math.round(windSpeed)} ${windUnit}`;
    document.getElementById("humidity").textContent =
      `${Math.round(humidity)}%`;
    document.getElementById("precipitation").textContent =
      `${Math.round(precipitation)} ${precipUnit}`;

    // 6️⃣ Render daily & hourly forecasts
    renderDailyForecast(result.daily, unitSymbol, current);
    renderHourlyForecast(result, unitSymbol);
  } catch (error) {
    console.error("Weather error:", error);
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

// Step 1: pass current weather to daily forecast [rendering function]
// 1️⃣ Grab the container for daily forecast boxes
// 2️⃣ Clear old daily forecast HTML
// 3️⃣ Loop through daily.time array (max 7 days)
// 4️⃣ For Day 1, use currentWeather for temperature and icon
// 5️⃣ For subsequent days, use daily array values from API
// 6️⃣ Create the HTML for each day and append to container

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
// Hourly forecast
function renderHourlyForecast(result, unitSymbol) {
  // 1️⃣ Grab the container
  const hourlyContainer = document.getElementById("hourlyForecast");
  const hourlyDaySelect = document.getElementById("hourlyDay");

  // 2️⃣ Clear old data
  hourlyContainer.innerHTML = "";
  hourlyDaySelect.innerHTML = "";

  // 🔹 Find the index of the current hour
  const now = new Date(result.current_weather.time);
  let startIndex = 0;

  for (let i = 0; i < result.hourly.time.length; i++) {
    const hourTime = new Date(result.hourly.time[i]);
    if (hourTime >= now) {
      startIndex = i;
      break;
    }
  }

  // 🔹 Step 0: update dropdown with current day
  const firstHour = new Date(result.hourly.time[startIndex]);
  const weekdayName = firstHour.toLocaleDateString("en-US", {
    weekday: "long",
  });

  const option = document.createElement("option");
  option.value = weekdayName;
  option.textContent = weekdayName;
  hourlyDaySelect.appendChild(option);
  hourlyDaySelect.value = weekdayName;

  // Update dropdown
  // const hourlyDaySelect = document.getElementById("hourlyDay");
  // hourlyDaySelect.innerHTML = ""; // clear old options
  // const option = document.createElement("option");
  // option.value = weekdayName;
  // option.textContent = weekdayName;
  // hourlyDaySelect.appendChild(option);
  // hourlyDaySelect.value = weekdayName;

  // Update header
  // const selectedDayEl = document.getElementById("hourlySelectedDay");
  // selectedDayEl.textContent = fullDate;

  // 3️⃣ Loop through the next 8 hours
  for (let i = startIndex; i < startIndex + 8; i++) {
    const timeString = result.hourly.time[i];
    if (!timeString) break; // safety check

    const time = new Date(timeString);
    const hour = time.getHours();
    const ampm = hour >= 12 ? "PM" : "AM";
    const formattedHour = hour % 12 || 12;
    // const now = new Date(); // current local time
    const temp = Math.round(result.hourly.temperature_2m[i]);
    const iconFile = getWeatherIconName(result.hourly.weather_code[i]);

    const hourEl = document.createElement("div");
    hourEl.className = "hourly__hour";

    // ✅ Highlight current hour
    if (
      time.getFullYear() === now.getFullYear() &&
      time.getMonth() === now.getMonth() &&
      time.getDate() === now.getDate() &&
      hour === now.getHours()
    ) {
      hourEl.classList.add("current");
    }

    hourEl.innerHTML = `
            <img class="hourly__hour-icon" src="/assets/images/${iconFile}" alt="" aria-hidden="true" />
            <p class="hourly__hour-time">${formattedHour}:00 ${ampm}</p>
            <p class="hourly__hour-temp">${temp}${unitSymbol}</p>
        `;

    hourlyContainer.appendChild(hourEl);
  }
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

// WHEN we get weatherCode <0> THEN it returns 'sunny'
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

  if (!weatherCodes[code]) {
    console.warn("Unknown weather code:", code);
  }

  const icon = weatherCodes[code] ?? "overcast";
  return `icon-${icon}.webp`;
}

// Initial load (optional: default city)
getGeoData("Rotterdam");
