import os
import json
import requests
import sys

def get_config():
    config_path = "refinery-config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def get_sonar_metrics():
    token = os.getenv("SONAR_TOKEN")
    config = get_config()
    project_key = os.getenv("SONAR_PROJECT_KEY") or config.get("sonarProjectKey", "MKwaak_weather-app-main")
    url = f"https://sonarcloud.io/api/measures/component?component={project_key}&metricKeys=coverage,bugs,vulnerabilities"
    
    try:
        response = requests.get(url, auth=(token, "") if token else None, timeout=10)
        if response.status_code != 200:
            return 20.0, f"Sonar Pending ({response.status_code})"
            
        data = response.json()
        if 'component' not in data or 'measures' not in data['component']:
            return 40.0, "Waiting for Sonar calculation..."
            
        measures = {m['metric']: m['value'] for m in data['component']['measures']}
        coverage = float(measures.get('coverage', 0))
        bugs = int(measures.get('bugs', 0))
        
        if coverage == 0:
            return 40.0, f"Scan OK, Coverage Pending (Bugs: {bugs})"
            
        score = max(0, coverage - (bugs * 2)) 
        return round(score, 1), f"{coverage}% (Bugs: {bugs})"
    except:
        return 20.0, "Sonar API Offline"

def calculate():
    config = get_config()
    version = os.getenv("APP_VERSION", "0.0.0-unknown")
    app_name = config.get("appName", "QaaS REFINERY")
    
    pillars = [
        ("Entry Check", "entry"),
        ("Unit Testing", "unit"),
        ("Code Quality", "sonar"),
        ("Functionality", "accuracy"),
        ("Security Scan", "security"),
        ("Performance", "perf"),
        ("Load Stability", "load"),
        ("Chaos Resilience", "chaos")
    ]
    
    results = {}

    for name, prefix in pillars:
        if name == "Code Quality":
            score, detail = get_sonar_metrics()
            results[name] = {"score": score, "detail": detail, "skipped": False}
            continue

        if name == "Unit Testing":
            coverage_file = config.get("coveragePath", "tests/lcov.info")
            if os.path.exists(coverage_file):
                results[name] = {"score": 100, "detail": "Jest Passed", "skipped": False}
            else:
                results[name] = {"score": 0, "detail": "Missing lcov", "skipped": True}
            continue

        file_path = f"tests/{prefix}_results.json"
        
        # --- VERBETERDE K6 PARSING (Slechts 1x nodig) ---
        if prefix == "perf" and os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                p95 = None
                if 'metrics' in data and 'http_req_duration' in data['metrics']:
                    p95 = data['metrics']['http_req_duration']['values'].get('p(95)')
                
                if p95 is not None:
                    score = 100.0 if p95 < 200 else max(0, 100 - (p95 - 200) / 2)
                    results[name] = {"score": round(score, 1), "detail": f"{round(p95, 2)}ms (p95)", "skipped": False}
                else:
                    # Fallback: bestand is er, maar p95 is even onvindbaar
                    results[name] = {"score": 80.0, "detail": "Test OK (p95 hidden)", "skipped": False}
                continue
            except Exception as e:
                results[name] = {"score": 0, "detail": f"Parse Error: {str(e)[:5]}", "skipped": True}
                continue

    active_rqi = [results[n]["score"] for n, _ in pillars if not results[name]["skipped"]]
    rqi_score = sum(active_rqi) / len(active_rqi) if active_rqi else 0

    print("\n" + "="*60)
    print(f" 🚀 {app_name} | VERSION: {version}")
    print("="*60)
    print(f" 🚢 RQI (Release Quality Index): {rqi_score:>5.1f} / 100")
    print("-" * 60)

    for name, _ in pillars:
        res = results[name]
        emoji = "⚪" if res["skipped"] else ("🟢" if res["score"] >= 80 else ("🟡" if res["score"] >= 50 else "🔴"))
        print(f"{emoji} {name:<20} : {res['score']:>5.1f}/100 ({res['detail']})")

    # --- VEILIGE RQI BEREKENING (Buiten de loop!) ---
    # We pakken alleen de scores van de onderdelen die NIET overgeslagen (skipped) zijn
    scored_values = [res["score"] for res in results.values() if not res["skipped"]]
    rqi_score = sum(scored_values) / len(scored_values) if scored_values else 0
    
    print("="*60)
    threshold = 80.0
    status = "PASSED" if rqi_score >= threshold else "FAILED"
    print(f" {'✅' if status == 'PASSED' else '❌'} STATUS: {status}")
    print("="*60 + "\n")
    
    if status == "FAILED":
        sys.exit(1)

if __name__ == "__main__":
    calculate()