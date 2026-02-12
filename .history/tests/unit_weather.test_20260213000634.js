/**
 * @jest-environment jsdom
 */

// 1. Fake de HTML-elementen die script.js direct nodig heeft bij het laden
document.body.innerHTML = `
  <select id="ddlUnits"></select>
  <div id="divCityCountry"></div>
  <div id="divCurrentDate"></div>
  <div id="divCurrentTemp"></div>
  <form class="hero__search">
    <input id="search" />
  </form>
  <div id="dailyForecast"></div>
  <div id="hourlyForecast"></div>
  <select id="hourlyDay"></select>
`;

// 2. Nu pas script.js inladen (nu vindt hij de elementen wel!)
const {
  selectLocation,
  getCityName,
  getWeatherIconName,
} = require("../script.js");

describe("Weather App Logic Tests", () => {
  test("EU Prioriteit: Moet NL kiezen boven US", () => {
    const mockData = [
      { address: { country_code: "us" } },
      { address: { country_code: "nl" } },
    ];

    const selected = selectLocation(mockData);
    expect(selected.address.country_code).toBe("nl");
  });

  test("Stadsnaam Logica: Moet de juiste naam pakken", () => {
    const mockAddress = { town: "Groot-Ammers" };
    expect(getCityName(mockAddress)).toBe("Groot-Ammers");
  });

  test("Icon Mapper: Code 0 moet sunny teruggeven", () => {
    expect(getWeatherIconName(0)).toBe("icon-sunny.webp");
  });
});
