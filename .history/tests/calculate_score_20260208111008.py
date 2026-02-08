import glob
import os
import json
import requests
import os

def get_sonar_status():
    # De publieke API van SonarCloud (omdat je repo Public is, kan dit zonder ingewikkelde auth)
    project_key = "MKwaak_weather-app-main"
    url = f"https://sonarcloud.io/api/qualitygates/project_status?projectKey={project_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        status = data['projectStatus']['status'] # Dit geeft 'OK' of 'ERROR'
        return status
    except Exception:
        return "UNKNOWN"

# In je score berekening:
sonar_res = get_sonar_status()
if sonar_res == "OK":
    scores['Code Quality'] = 100
    details.append("Pillar 5: Code Quality PASSED (SonarCloud Quality Gate OK)")
else:
    scores['Code Quality'] = 0
    details.append(f"Pillar 5: Code Quality FAILED (Status: {sonar_res})")

def calculate():
    scores = {}
    details = []

    def get_latest_data(prefix):
        file_path = f"tests/{prefix}_results.json"
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None

    # 1. Performance Score (Baseline)
    # Target: < 200ms is 100 punten. Elke 10ms daarboven is -1 punt.
    perf_data = get_latest_data('perf')
    if perf_data:
        # Zoek naar de p95, kijk zowel in 'values' als direct in de metric
        metric = perf_data['metrics'].get('http_req_duration', {})
        values = metric.get('values', metric) # Fallback naar de metric zelf
        p95 = values.get('p(95)', 0)
        
        if p95 <= 200:
            p_score = 100
        else:
            p_score = max(0, 100 - int((p95 - 200) / 10))
        scores['Performance'] = p_score
        details.append(f"Performance Index: {p_score}/100 (Latency: {p95:.2f}ms)")
    else:
        scores['Performance'] = 0
        details.append("Performance: No data found (0/100)")
    
    # 2. Load Stability Score
    load_data = get_latest_data('load_test')
    if load_data:
        # Veilig de metric ophalen
        metric = load_data['metrics'].get('http_req_failed', {})
        values = metric.get('values', metric) # Gebruik 'values' of de metric zelf
        fail_rate = values.get('rate', 0)      # Fallback naar 0 bij twijfel
        
        l_score = int((1.0 - fail_rate) * 100)
        scores['Load'] = l_score
        details.append(f"Load Stability Index: {l_score}/100 (Success Rate: {(1.0-fail_rate)*100:.2f}%)")
    else:
        scores['Load'] = 0
        details.append("Load: No data found (0/100)")

    # 3. Chaos Resilience Score
    chaos_data = get_latest_data('chaos')
    if chaos_data:
        # Veilig de metric ophalen
        metric = chaos_data['metrics'].get('http_req_failed', {})
        values = metric.get('values', metric)
        fail_rate = values.get('rate', 0)
        
        c_score = int((1.0 - fail_rate) * 100)
        scores['Chaos'] = c_score
        details.append(f"Chaos Resilience Index: {c_score}/100 (Availability: {(1.0-fail_rate)*100:.2f}%)")
    else:
        scores['Chaos'] = 0
        details.append("Chaos: No data found (0/100)")

    # 4. Security Score
    # 0 vulns = 100 punten. Elke vuln is -10 punten.
    try:
        with open('tests/security_results.json', 'r') as f:
            sec_data = json.load(f)
            vulns = len(sec_data.get('Results', [{}])[0].get('Vulnerabilities', []))
            s_score = max(0, 100 - (vulns * 10))
            scores['Security'] = s_score
            details.append(f"Security Index: {s_score}/100 ({vulns} vulnerabilities)")
    except:
        scores['Security'] = 0
        details.append("Security: Not scanned (0/100)")

    # Gemiddelde berekenen
    final_index = sum(scores.values()) / len(scores)

    # --- OUTPUT ---
    print("\n" + "="*45)
    print(f" 🏆 WEATHER APP QUALITY DASHBOARD")
    print("="*45)
    for d in details:
        print(f"- {d}")
    print("-" * 45)
    print(f" FINAL QUALITY INDEX: {final_index:.1f} / 100")
    print("="*45 + "\n")

    # GitHub Step Summary (Mooie tabel voor in de UI)
    summary_file = os.getenv('GITHUB_STEP_SUMMARY')
    if summary_file:
        with open(summary_file, 'a') as f:
            f.write(f"## 🏆 Quality Dashboard (Run {os.getenv('GITHUB_RUN_NUMBER')})\n")
            f.write(f"### **Final Quality Index: {final_index:.1f} / 100**\n\n")
            f.write("| Pillar | Score | Details |\n")
            f.write("| :--- | :--- | :--- |\n")
            for pillar, score in scores.items():
                detail_text = [d for d in details if pillar in d][0]
                status_emoji = "🟢" if score > 90 else "🟡" if score > 70 else "🔴"
                f.write(f"| {status_emoji} {pillar} | **{score}** | {detail_text.split(': ')[1]} |\n")

if __name__ == "__main__":
    calculate()