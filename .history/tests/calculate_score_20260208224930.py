import os
import json
import requests

def get_sonar_status():
    """Haalt de live status op van de SonarCloud Quality Gate met authenticatie."""
    # We halen de token uit de environment variabelen van de GitHub Action
    token = os.getenv("SONAR_TOKEN")
    project_key = "MKwaak_weather-app-main"
    url = f"https://sonarcloud.io/api/qualitygates/project_status?projectKey={project_key}"
    
    try:
        # SonarCloud wil de token als 'username' bij Basic Auth, met een leeg wachtwoord
        if token:
            response = requests.get(url, auth=(token, ""), timeout=10)
        else:
            # Fallback als de token lokaal niet is ingesteld
            response = requests.get(url, timeout=10)
            
        data = response.json()
        status = data['projectStatus']['status'] # 'OK' of 'ERROR'
        
        # Kleine extra check voor ons dashboard
        if status == "OK":
            return "OK"
        else:
            print(f"DEBUG: SonarCloud status is {status}")
            return "FAILED"
            
    except Exception as e:
        print(f"SonarCloud API Error: {e}")
        return "UNKNOWN"

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

    # --- 1. Performance Score ---
    perf_data = get_latest_data('perf')
    if perf_data:
        metric = perf_data['metrics'].get('http_req_duration', {})
        values = metric.get('values', metric)
        p95 = values.get('p(95)', 0)
        p_score = 100 if p95 <= 200 else max(0, 100 - int((p95 - 200) / 10))
        scores['Performance'] = p_score
        details.append(f"Performance Index: {p_score}/100 (Latency: {p95:.2f}ms)")
    else:
        scores['Performance'] = 0
        details.append("Performance: No data found (0/100)")
    
    # --- 2. Load Stability Score ---
    load_data = get_latest_data('load_test')
    if load_data:
        metric = load_data['metrics'].get('http_req_failed', {})
        values = metric.get('values', metric)
        fail_rate = values.get('rate', 0)
        l_score = int((1.0 - fail_rate) * 100)
        scores['Load'] = l_score
        details.append(f"Load Stability Index: {l_score}/100 (Success Rate: {(1.0-fail_rate)*100:.2f}%)")
    else:
        scores['Load'] = 0
        details.append("Load: No data found (0/100)")

    # --- 3. Chaos Resilience Score ---
    chaos_data = get_latest_data('chaos')
    if chaos_data:
        metric = chaos_data['metrics'].get('http_req_failed', {})
        values = metric.get('values', metric)
        fail_rate = values.get('rate', 0)
        c_score = int((1.0 - fail_rate) * 100)
        scores['Chaos'] = c_score
        details.append(f"Chaos Resilience Index: {c_score}/100 (Availability: {(1.0-fail_rate)*100:.2f}%)")
    else:
        scores['Chaos'] = 0
        details.append("Chaos Resilience: No data found (0/100)")

    # --- 4. Security Score (Trivy) ---
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

    # --- 5. Code Quality Score (SonarCloud) ---
    sonar_res = get_sonar_status()
    if sonar_res == "OK":
        sq_score = 100
        status_msg = "PASSED"
    elif sonar_res == "ERROR":
        sq_score = 0
        status_msg = "FAILED"
    else:
        sq_score = 50 # Neutraal bij onbekende status
        status_msg = "UNKNOWN"
    
    scores['Code Quality'] = sq_score
    details.append(f"Code Quality Index: {sq_score}/100 (SonarCloud Quality Gate: {status_msg})")

    # --- TOTAAL BEREKENING ---
    final_index = sum(scores.values()) / len(scores)

    # --- TERMINAL OUTPUT ---
    print("\n" + "="*45)
    print(f" 🏆 WEATHER APP QUALITY DASHBOARD")
    print("="*45)
    for d in details:
        print(f"- {d}")
    print("-" * 45)
    print(f" FINAL QUALITY INDEX: {final_index:.1f} / 100")
    print("="*45 + "\n")

    # --- GITHUB SUMMARY TABLE ---
    summary_file = os.getenv('GITHUB_STEP_SUMMARY')
    if summary_file:
        with open(summary_file, 'a') as f:
            f.write(f"## 🏆 Quality Dashboard (Run {os.getenv('GITHUB_RUN_NUMBER')})\n")
            f.write(f"### **Final Quality Index: {final_index:.1f} / 100**\n\n")
            f.write("| Pillar | Score | Details |\n")
            f.write("| :--- | :--- | :--- |\n")
            # We loopen door de scores om de tabel te vullen
            for pillar, score in scores.items():
                # Zoek de bijbehorende detail-regel
                detail_text = next((d for d in details if pillar in d), "Geen details")
                # Strip de prefix voor een schone tabel
                clean_detail = detail_text.split(': ')[1] if ': ' in detail_text else detail_text
                
                status_emoji = "🟢" if score > 90 else "🟡" if score > 50 else "🔴"
                f.write(f"| {status_emoji} {pillar} | **{score}** | {clean_detail} |\n")

if __name__ == "__main__":
    calculate()