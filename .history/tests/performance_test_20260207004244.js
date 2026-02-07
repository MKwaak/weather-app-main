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
  // Gebruik de juiste poort van je tunnel
  const url = __ENV.TEST_URL || "http://127.0.0.1:31234";
  const res = http.get(url);

  check(res, {
    "status is 200": (r) => r.status === 200,
    // De veilige check: check eerst of r en r.body bestaan
    "versie is zichtbaar": (r) => r && r.body && r.body.includes("v1.0.0"),
  });

  sleep(1);
}
