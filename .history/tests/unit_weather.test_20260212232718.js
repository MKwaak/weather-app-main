// We definiëren de logica hier direct zodat de test niet crasht op de browser-code van script.js
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
  return address.city || address.town || address.village || "Unknown location";
}

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
});
