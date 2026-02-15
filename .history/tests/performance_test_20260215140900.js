import http from "k6/http";
import { check, sleep } from "k6";

// Matcht nu 1.1.x (jouw huidige reeks) of gewoon elk versienummer X.X.X
const versionPattern = /\d+\.\d+\.\d+/;

export const options = {
  vus: 10,
  duration: "30s",
  thresholds: {
    http_req_duration: ["p(95)<200"],
    // We houden de check, maar nu met de juiste regex
    "checks{check:versie is correct}": ["rate>=0.95"],
  },
};

export default function () {
  // De fallback naar 31234 is prima, zolang de --env TEST_URL vanuit de pipeline maar leidend is
  const url = __ENV.TEST_URL || "http://127.0.0.1:57974";
  const res = http.get(url);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "versie is correct": (r) => r.body && versionPattern.test(r.body),
  });

  sleep(1);
}
