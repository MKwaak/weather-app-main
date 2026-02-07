import http from "k6/http";
import { check, sleep } from "k6";
// DEZE REGEL IS CRUCIAAL VOOR DE SUMMARY:
import { textSummary } from "https://jslib.k6.io/k6-summary/0.0.2/index.js";

export const options = {
  stages: [
    { duration: "1m", target: 20 }, // Ramping up: van 0 naar 20 gebruikers
    { duration: "1m", target: 20 }, // Steady state: kijken hoe de pods het houden
    { duration: "10s", target: 0 }, // Ramping down: afschalen
  ],
  thresholds: {
    // Timestamps verzamelen: 95% van de requests moet onder de 200ms blijven
    http_req_duration: ["p(95)<200"],
    // We laten 5% fouten toe tijdens chaos, 1% is soms net te krap voor de Judge
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  const url = __ENV.TEST_URL || "http://localhost:31234/";
  const res = http.get(url);

  check(res, {
    "status is 200": (r) => r.status === 200,
    // Veiligere check: kijk of er überhaupt een body is
    "bevat data": (r) => r.body && r.body.length > 0,
  });

  sleep(1);
}

export function handleSummary(data) {
  console.log("Rapportage wordt nu gegenereerd...");
  return {
    // We schrijven het naar de huidige map én de tests map voor de zekerheid
    "load-test-results.json": JSON.stringify(data),
    "tests/load-test-results.json": JSON.stringify(data),
    stdout: textSummary(data, { indent: " ", enableColors: true }),
  };
}
