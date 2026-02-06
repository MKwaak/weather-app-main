import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "30s", target: 20 }, // Ramping up: van 0 naar 20 gebruikers
    { duration: "1m", target: 20 }, // Steady state: kijken hoe de pods het houden
    { duration: "30s", target: 0 }, // Ramping down: afschalen
  ],
  thresholds: {
    // Timestamps verzamelen: 95% van de requests moet onder de 200ms blijven
    http_req_duration: ["p(95)<200"],
    // We tolereren geen fouten (0% error rate)
    http_req_failed: ["rate<0.01"],
  },
};

export default function () {
  // Pak de URL uit de environment variabele die we in de YAML meegeven
  const url = __ENV.TEST_URL || "http://localhost:31234/";
  const res = http.get(url);
  // ... rest van je test ...
  check(res, {
    "status is 200": (r) => r.status === 200,
    "bevat versie tag": (r) => r.body.includes('id="version-tag"'),
  });

  sleep(1); // Simuleer rusttijd van de gebruiker
}
