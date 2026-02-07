import http from "k6/http";
import { check, sleep } from "k6";

// DEZE MOET ERBIJ:
const versionPattern = /2\.0\.\d+/;

export const options = {
  vus: 10,
  duration: "30s",
  thresholds: {
    http_req_duration: ["p(95)<200"],
    // Optioneel: voeg deze toe zodat de Judge ook hier de check ziet
    "checks{check:versie is correct}": ["rate>=0.95"],
  },
};

export default function () {
  const url = __ENV.TEST_URL || "http://127.0.0.1:31234";
  const res = http.get(url);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "versie is correct": (r) => r.body && versionPattern.test(r.body),
  });

  sleep(1);
}
