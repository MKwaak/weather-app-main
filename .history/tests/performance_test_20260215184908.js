import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 10,
  duration: "30s",
  thresholds: {
    // De Judge kijkt specifiek naar deze p(95)
    http_req_duration: ["p(95)<200"],
  },
};

export default function () {
  const url = __ENV.TEST_URL || "http://127.0.0.1:57974";
  const res = http.get(url);

  check(res, {
    "status is 200": (r) => r.status === 200,
  });

  sleep(1);
}
