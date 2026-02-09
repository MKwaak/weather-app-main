import os
import json
import requests
import glob

def get_sonar_status():
    """Haalt de live status op van de SonarCloud Quality Gate."""
    token = os.getenv("SONAR_TOKEN")
    project_key = "MKwaak_weather-app-main"
    url = f"https://sonarcloud.io/api/qualitygates/project_status?projectKey={project_key}"
    try:
        response = requests.get(url, auth=(token, "") if token else None, timeout=10)
        data = response.json()
        return data['projectStatus']['status'] # 'OK' of 'ERROR'
    except:
        return "UNKNOWN"

def calculate():
    # Configuratie van de Pilaren
    # (Naam in Dashboard, Prefix van JSON bestand)
    pillars = [
        ("Performance", "perf"),
        ("Load Stability", "load"),
        ("Chaos Resilience", "chaos"),
        ("Security Scan", "security"),
        ("Location Accuracy", "functional")
    ]
    
    results = {}
    total_score = 0
    
    # 1. Haal data op voor de eerste 5 pilaren (JSON gebaseerd)
    for name, prefix in pillars:
        file_path = f"{prefix}_results.json"
        # Check ook in 'tests/' voor lokale runs
        if not os.path.exists(file_path):
            file_path = f"tests/{file_path}"

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Score extractie logica
                    if prefix == 'security':
                        vulns = len(data.get('Results', [{}])[0].get('Vulnerabilities', []))
                        score = max(0, 100 - (vulns * 10))
                        detail = f"{vulns} vulnerabilities found"
                    elif prefix == 'functional':
                        score = data.get('score', 0)
                        detail = f"Accuracy: {score}%"
                    else: # k6 tests (perf, load, chaos)
                        metric = data['metrics'].get('http_req_failed', data['metrics'].get('http_req_duration', {}))
                        values = metric.get('values', metric)
                        if 'rate' in values: # Failure rate based
                            score = int((1.0 - values['rate']) * 100)
                            detail = f"Success Rate: {(1.0-values['rate'])*100:.1f}%"
                        else: # Latency based (perf)
                            p95 = values.get('p(95)', 0)
                            score = 100 if p95 <= 200 else max(0, 100 - int((p95 - 200) / 10))
                            detail = f"p95 Latency: {p95:.2f}ms"
                    
                    results[name] = {"score": score, "detail": detail, "skipped": False}
                    total_score += score
            except:
                results[name] = {"score": 0, "detail": "Data error", "skipped": True}
        else:
            results[name] = {"score": 0, "detail": "Skipped", "skipped": True}

    # 2. SonarCloud apart (Pilaar 6)
    sonar_res = get_sonar_status()
    s_score = 100 if sonar_res == "OK" else (50 if sonar_res == "UNKNOWN" else 0)
    results["Code Quality"] = {
        "score": s_score, 
        "detail": f"SonarCloud: {sonar_res}", 
        "skipped": False if sonar_res != "UNKNOWN" else True
    }
    total_score += s_score

    # 3. Bereken Release Quality Index (RQI)
    # Altijd delen door 6 (het volledige examen)
    rqi = total_score / 6

    # --- TERMINAL OUTPUT ---
    print("\n" + "="*50)
    print(f" 🚀 QaaS - RELEASE QUALITY DASHBOARD")
    print("="*50)
    
    for name, data in results.items():
        icon = "⚪" if data['skipped'] else ("🟢" if data['score'] >= 90 else "🟡" if data['score'] >= 50 else "🔴")
        print(f"{icon} {name:<18} : {data['score']:>3}/100 ({data['detail']})")
    
    print("-" * 50)
    print(f" RELEASE QUALITY INDEX (RQI): {rqi:.1f} / 100")
    print("="*50)
    
    status_msg = "✅ RELEASE CANDIDATE APPROVED" if rqi >= 80 else "⚠️ NOT READY FOR RELEASE"
    print(f" STATUS: {status_msg}")
    print("="*50 + "\n")

    # --- GITHUB SUMMARY ---
    summary_file = os.getenv('GITHUB_STEP_SUMMARY')
    if summary_file:
        with open(summary_file, 'a') as f:
            f.write(f"## 🚀 Release Quality Dashboard (RQI)\n")
            f.write(f"### **RQI Score: {rqi:.1f} / 100**\n\n")
            f.write("| Pillar | Status | Score | Details |\n| :--- | :---: | :---: | :--- |\n")
            for name, data in results.items():
                icon = "⚪" if data['skipped'] else ("🟢" if data['score'] >= 90 else "🟡" if data['score'] >= 50 else "🔴")
                f.write(f"| {name} | {icon} | **{data['score']}** | {data['detail']} |\n")
            f.write(f"\n**Final Verdict: {status_msg}**\n")

if __name__ == "__main__":
    calculate()