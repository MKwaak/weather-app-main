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
  // Gebruik de URL van je Minikube tunnel
  const res = http.get("http://127.0.0.1:52428");

  check(res, {
    "status is 200": (r) => r.status === 200,
    "versie is zichtbaar": (r) => r.body.includes("version-tag"),
  });

  sleep(1); // Simuleer rusttijd van de gebruiker
}
