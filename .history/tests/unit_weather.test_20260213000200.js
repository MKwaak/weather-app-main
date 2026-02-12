/**
 * @jest-environment jsdom
 */

// We halen de functies direct uit script.js
const {
  selectLocation,
  getCityName,
  getWeatherIconName,
} = require("../script.js");

describe("Weather App Logic Tests", () => {
  test("EU Prioriteit: Moet NL kiezen boven US uit de echte script.js", () => {
    const mockData = [
      { address: { country_code: "us" } },
      { address: { country_code: "nl" } },
    ];

    // We roepen de functie nu direct aan
    const selected = selectLocation(mockData);
    expect(selected.address.country_code).toBe("nl");
  });

  test("Stadsnaam Logica: Moet de juiste naam pakken uit de echte script.js", () => {
    const mockAddress = { town: "Groot-Ammers" };
    expect(getCityName(mockAddress)).toBe("Groot-Ammers");
  });

  test("Icon Mapper: Code 0 moet sunny teruggeven", () => {
    expect(getWeatherIconName(0)).toBe("icon-sunny.webp");
  });
});
