import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  // Scenario: 10 gebruikers surfen tegelijkertijd voor 30 seconden
  vus: 10,
  duration: "30s",
  thresholds: {
    // Quality Gate: 95% van de verzoeken moet sneller zijn dan 200ms
    http_req_duration: ["p(95)<200"],
  },
};

export default function () {
  // Pak de URL uit de environment variabele die we in de YAML meegeven
  const url = __ENV.TEST_URL || "http://localhost:8080, http://127.0.0.1:52428";
  const res = http.get(url);
  // ... rest van je test ...
  check(res, {
    "status is 200": (r) => r.status === 200,
    "versie is zichtbaar": (r) => r.body.includes("version-tag"),
  });

  sleep(1); // Simuleer rusttijd van de gebruiker
}
