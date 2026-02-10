import os
import json
import requests

def get_current_version():
    version = os.getenv("APP_VERSION")
    if version and version.strip():
        return version
    if os.path.exists("VERSION"):
        try:
            with open("VERSION", "r") as f:
                v = f.read().strip()
                if v: return v
        except: pass
    return "2.2.0"

def get_sonar_status():
    token = os.getenv("SONAR_TOKEN")
    project_key = "MKwaak_weather-app-main"
    url = f"https://sonarcloud.io/api/qualitygates/project_status?projectKey={project_key}"
    try:
        response = requests.get(url, auth=(token, "") if token else None, timeout=10)
        data = response.json()
        status = data['projectStatus']['status']
        return "OK" if status in ["OK", "ERROR"] else "FAILED"
    except:
        return "UNKNOWN"

def calculate():
    # JOUW NIEUWE VOLGORDE
    pillars = [
        ("Entry Check", "entry"),
        ("Code Quality", "sonar"),
        ("Functionality", "accuracy"),
        ("Security Scan", "security"),
        ("Performance", "perform"),
        ("Load Stability", "load"),
        ("Chaos Resilience", "chaos")
    ]
    
    results = {}
    version = get_current_version()

    for name, prefix in pillars:
        if name == "Code Quality":
            status = get_sonar_status()
            results[name] = {"score": 100 if status == "OK" else 0, "detail": f"Sonar: {status}", "skipped": status == "UNKNOWN"}
            continue

        # Match de bestandsnaam (bijv tests/accuracy_results.json)
        file_path = f"tests/{prefix}_results.json"
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    score = data.get('score', 0)
                    
                    if prefix == 'entry':
                        detail = data.get('detail', 'Up')
                    elif prefix == 'accuracy':
                        detail = f"Accuracy: {score}%"
                    elif prefix == 'security':
                        vulns = len(data.get('Results', [{}])[0].get('Vulnerabilities', []))
                        score = max(0, 100 - (vulns * 10))
                        detail = f"{vulns} vulnerabilities"
                    elif prefix == 'perform':
                        metrics = data.get('metrics', {})
                        p95 = metrics.get('http_req_duration', {}).get('values', {}).get('p(95)', 0)
                        score = 100 if p95 <= 200 and p95 > 0 else max(0, 100 - int(p95/10))
                        detail = f"p95: {p95:.2f}ms"
                    else: # load & chaos
                        metrics = data.get('metrics', {})
                        rate = metrics.get('http_req_failed', {}).get('values', {}).get('rate', 1.0)
                        score = int((1.0 - rate) * 100)
                        detail = f"Success: {score}%"
                    
                    results[name] = {"score": score, "detail": detail, "skipped": False}
            except:
                results[name] = {"score": 0, "detail": "Data error", "skipped": True}
        else:
            results[name] = {"score": 0, "detail": "Skipped", "skipped": True}

    # CQI: De eerste 4 (Deployment & Code)
    cqi_names = ["Entry Check", "Code Quality", "Functionality", "Security Scan"]
    active_cqi = [results[n]["score"] for n in cqi_names if not results[n]["skipped"]]
    cqi_score = sum(active_cqi) / len(active_cqi) if active_cqi else 0

    # RQI: Alles (Release Readiness)
    rqi_score = sum(results[n]["score"] for n, _ in pillars) / len(pillars)

    # OUTPUT
    print("\n" + "="*60)
    print(f" 🚀 QaaS - QUALITY DASHBOARD | VERSION: {version}")
    print("="*60)
    print(f" 🛠️  CQI (Code Quality Index)   : {cqi_score:>5.1f} / 100")
    print(f" 🚢 RQI (Release Quality Index): {rqi_score:>5.1f} / 100")
    print("-" * 60)
    for name, _ in pillars:
        res = results[name]
        emoji = "⚪" if res["skipped"] else ("🟢" if res["score"] >= 90 else "🟡" if res["score"] >= 70 else "🔴")
        print(f"{emoji} {name:<20} : {res['score']:>3}/100 ({res['detail']})")
    print("="*60 + "\n")

    return version, cqi_score, rqi_score

if __name__ == "__main__":
    ver, cqi, rqi = calculate()
    with open("quality_history.csv", "a") as f:
        f.write(f"{ver},{cqi:.1f},{rqi:.1f}\n")