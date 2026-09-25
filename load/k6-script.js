import http from 'k6/http';
import { check, sleep } from 'k6';

// k6 load test configuration to trigger backend HPA scaling
export const options = {
  stages: [
    { duration: '30s', target: 10 },  // warm-up to 10 VUs
    { duration: '1m', target: 50 },   // ramp up to 50 VUs (generate CPU pressure)
    { duration: '2m', target: 100 },  // sustain 100 VUs to breach 60% CPU target
    { duration: '1m', target: 10 },   // step down
    { duration: '30s', target: 0 },   // cooldown
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests must complete below 2s
    http_req_failed: ['rate<0.05'],    // less than 5% failure rate
  },
};

const BASE_URL = __ENV.TARGET_URL || 'http://localhost:8000';

const SAMPLE_COMPLAINTS = [
  {
    text: "Water supply pipeline broken near market chowk causing heavy flooding on main road.",
    location: "Gulshan Block 5, Karachi",
    reporter_contact: "0300-1234567"
  },
  {
    text: "Severe electricity outage in sector G-9 for the last 6 hours, transformers making sparking noises.",
    location: "Sector G-9/2, Islamabad",
    reporter_contact: "0321-7654321"
  },
  {
    text: "Open manhole uncovered in residential street creating extreme hazard for pedestrians at night.",
    location: "Model Town Block C, Lahore",
    reporter_contact: "0333-9876543"
  },
  {
    text: "Garbage accumulation blocking drainage line, foul smell and sanitation crisis.",
    location: "Saddar Bazaar, Rawalpindi",
    reporter_contact: null
  }
];

export default function () {
  // 1. Fetch complaints list (database query pressure)
  const listRes = http.get(`${BASE_URL}/api/complaints?page=1&page_size=20`);
  check(listRes, {
    'list status is 200': (r) => r.status === 200,
  });

  // 2. Fetch aggregate stats
  const statsRes = http.get(`${BASE_URL}/api/stats`);
  check(statsRes, {
    'stats status is 200': (r) => r.status === 200,
  });

  // 3. Post a new complaint (simulated triage computation)
  const payload = JSON.stringify(SAMPLE_COMPLAINTS[Math.floor(Math.random() * SAMPLE_COMPLAINTS.length)]);
  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const postRes = http.post(`${BASE_URL}/api/complaints`, payload, params);
  check(postRes, {
    'post status is 201 or 429 (rate-limited)': (r) => r.status === 201 || r.status === 429,
  });

  sleep(0.1);
}
