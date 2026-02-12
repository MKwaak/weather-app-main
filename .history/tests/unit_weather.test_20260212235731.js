/**
 * @jest-environment jsdom
 */

// We importeren de functies uit het echte script.js bestand
const {
  selectLocation,
  getCityName,
  getWeatherIconName,
} = require("../script.js");

describe("Weather App Logic Tests (Integration with script.js)", () => {
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
    const icon = getWeatherIconName(0);
    expect(icon).toBe("icon-sunny.webp");
  });
});
