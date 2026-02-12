// Importeer de functies uit je echte script
// We gebruiken een try-catch omdat de rest van script.js (met fetch/DOM)
// in Node.js errors kan geven.
let weatherApp;
try {
  weatherApp = require("../script.js");
} catch (e) {
  // We negeren errors over document/window tijdens de import
}

describe("Weather App Logic Tests", () => {
  test("EU Prioriteit: Moet NL kiezen boven US", () => {
    const mockData = [
      { address: { country_code: "us" } },
      { address: { country_code: "nl" } },
    ];
    // Gebruik de logica die we uit script.js hebben gehaald
    const selected = weatherApp.selectLocation(mockData);
    expect(selected.address.country_code).toBe("nl");
  });
});
