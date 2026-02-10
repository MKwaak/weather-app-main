import os
import json
import requests
import sys

def get_sonar_status():
    token = os.getenv("SONAR_TOKEN")
    project_key = "MKwaak_weather-app-main"
    url = f"https://sonarcloud.io/api/qualitygates/project_status?projectKey={project_key}"
    try:
        response = requests.get(url, auth=(token, "") if token else None, timeout=10)
        data = response.json()
        return "OK" if data['projectStatus']['status'] == "OK" else "ERROR"
    except Exception as e:
        return "UNKNOWN"

def calculate():
    # 1. Dynamische input vanuit Environment Variables
    version = os.getenv("APP_VERSION", "0.0.0-unknown")
    override_reason = os.getenv("OVERRIDE_REASON", "")
    
    # 2. De 7 Pilaren van Kwaliteit
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

    # 3. Data verzamelen
    for name, prefix in pillars:
        if name == "Code Quality":
            status = get_sonar_status()
            results[name] = {
                "score": 100 if status == "OK" else 0, 
                "detail": f"Sonar: {status}", 
                "skipped": status == "UNKNOWN"
            }
            continue

        file_path = f"tests/{prefix}_results.json"
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    score = data.get('score', 0)
                    
                    # Detail extractie per type test
                    if prefix == 'entry':
                        detail = data.get('detail', 'Up')
                    elif prefix == 'accuracy':
                        detail = f"Acc: {score}%"
                    elif prefix == 'security':
                        # Trivy JSON parsing
                        results_list = data.get('Results', [])
                        vulns = 0
                        for r in results_list:
                            vulns += len(r.get('Vulnerabilities', []))
                        score = max(0, 100 - (vulns * 10))
                        detail = f"{vulns} issues"
                    else:
                        detail = f"Score: {score}%"
                    
                    results[name] = {"score": score, "detail": detail, "skipped": False}
            except:
                results[name] = {"score": 0, "detail": "Format error", "skipped": True}
        else:
            results[name] = {"score": 0, "detail": "Skipped", "skipped": True}

    # 4. CQI & RQI Berekening
    cqi_names = ["Entry Check", "Code Quality", "Functionality", "Security Scan"]
    active_cqi = [results[n]["score"] for n in cqi_names if not results[n]["skipped"]]
    cqi_score = sum(active_cqi) / len(active_cqi) if active_cqi else 0
    
    rqi_score = sum(results[n]["score"] for n, _ in pillars) / len(pillars)

    # 5. Dashboard Output
    print("\n" + "="*60)
    print(f" 🚀 QaaS - QUALITY DASHBOARD | VERSION: {version}")
    if override_reason:
        print(f" 🟦 STAKEHOLDER OVERRIDE: {override_reason}")
    print("="*60)
    print(f" 🛠️  CQI (Code Quality Index)   : {cqi_score:>5.1f} / 100")
    print(f" 🚢 RQI (Release Quality Index): {rqi_score:>5.1f} / 100")
    print("-" * 60)

    for name, _ in pillars:
        res = results[name]
        if res["skipped"]:
            emoji = "⚪"
        elif res["score"] >= 90:
            emoji = "🟢"
        elif res["score"] >= 70:
            emoji = "🟡"
        else:
            emoji = "🔴"
        print(f"{emoji} {name:<20} : {res['score']:>3}/100 ({res['detail']})")
    
    print("="*60)

    # 6. Besluitvorming (Quality Gate)
    threshold = 80.0
    is_passed = rqi_score >= threshold

    if override_reason:
        print(f" ✅ STATUS: PASSED BY OVERRIDE")
        final_status = "OVERRIDDEN"
    elif is_passed:
        print(f" ✅ STATUS: PASSED")
        final_status = "PASS"
    else:
        print(f" ❌ STATUS: FAILED (RQI below {threshold}%)")
        final_status = "FAIL"
    print("="*60 + "\n")

    # 7. Historie Loggen
    try:
        with open("quality_history.csv", "a") as f:
            f.write(f"{version},{cqi_score:.1f},{rqi_score:.1f},{final_status},\"{override_reason}\"\n")
    except:
        pass

    # Exit code voor de pipeline
    if not is_passed and not override_reason:
        # sys.exit(1) # Optioneel: zet dit aan om de pipeline echt te laten falen
        pass

if __name__ == "__main__":
    calculate()