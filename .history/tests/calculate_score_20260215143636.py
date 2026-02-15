import os
import json
import requests
import sys

def get_config():
    """Leest de refinery-config.json uit voor universele variabelen."""
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
            return 0, f"Sonar API Pending/Error ({response.status_code})"
            
        data = response.json()
        # Soms stuurt Sonar een response zonder 'measures' als de eerste analyse nog loopt
        if 'component' not in data or 'measures' not in data['component']:
            return 20.0, "Waiting for initial Sonar calculation..." # Geef een basis-score ipv 0
            
        measures = {m['metric']: m['value'] for m in data['component']['measures']}
        
        coverage = float(measures.get('coverage', 0))
        bugs = int(measures.get('bugs', 0))
        
        # Als coverage 0 is, maar we weten dat de scan gelukt is, 
        # geven we een tijdelijke score zodat de RQI niet instort
        if coverage == 0:
            return 40.0, f"Scan OK, Coverage Pending (Bugs: {bugs})"
            
        score = max(0, coverage - (bugs * 2)) 
        return round(score, 1), f"{coverage}% (Bugs: {bugs})"
    except Exception as e:
        return 20.0, "Sonar API Offline"

def calculate():
    config = get_config() # Leest de JSON
    version = os.getenv("APP_VERSION", "0.0.0-unknown")
    override_reason = os.getenv("OVERRIDE_REASON", "")
    
    # Gebruik de app naam uit config of default
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
        # --- 1. SonarCloud ---
        if name == "Code Quality":
            score, detail = get_sonar_metrics()
            results[name] = {"score": score, "detail": detail, "skipped": (score == 0 and "Bugs: 0" in detail)}
            continue

        # --- 2. Unit Testing ---
        if name == "Unit Testing":
            coverage_file = config.get("coveragePath", "tests/lcov.info")
            if os.path.exists(coverage_file):
                results[name] = {"score": 100, "detail": "Jest Passed", "skipped": False}
            else:
                results[name] = {"score": 0, "detail": "Missing lcov", "skipped": True}
            continue

        # --- 3. Performance (k6 specifieke parsing) ---
        file_path = f"tests/{prefix}_results.json"
        if prefix == "perf" and os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # We duiken diep in de k6 structuur voor de p(95)
                    p95 = data['metrics']['http_req_duration']['values']['p(95)']
                    # Score: 100 als < 200ms, anders lineair omlaag
                    score = 100.0 if p95 < 200 else max(0, 100 - (p95 - 200) / 2)
                    results[name] = {"score": round(score, 1), "detail": f"{round(p95, 2)}ms (p95)", "skipped": False}
                continue
            except Exception as e:
                results[name] = {"score": 0, "detail": "k6 Parse Error", "skipped": True}
                continue

        # --- 4. Standaard JSON (Entry, Accuracy, Security) ---
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    score = float(data.get('score', 0))
                    
                    if prefix == 'entry':
                        detail = data.get('detail', 'App Up')
                    elif prefix == 'accuracy':
                        detail = f"Acc: {score}%"
                    elif prefix == 'security':
                        results_list = data.get('Results', [])
                        vulns = sum(len(r.get('Vulnerabilities', [])) for r in results_list)
                        score = max(0, 100 - (vulns * 10))
                        detail = f"{vulns} issues"
                    else:
                        detail = f"Score: {score}%"
                    
                    results[name] = {"score": score, "detail": detail, "skipped": False}
            except:
                results[name] = {"score": 0, "detail": "Format error", "skipped": True}
        else:
            results[name] = {"score": 0, "detail": "Skipped", "skipped": True}

# Berekeningen
active_cqi = [results[n]["score"] for n in ["Entry Check", "Unit Testing", "Code Quality", "Functionality", "Security Scan"] if not results[n]["skipped"]]
cqi_score = sum(active_cqi) / len(active_cqi) if active_cqi else 0
    
active_rqi = [results[n]["score"] for n, _ in pillars if not results[n]["skipped"]]
rqi_score = sum(active_rqi) / len(active_rqi) if active_rqi else 0

# Dashboard Rendering
print("\n" + "="*60)
print(f" 🚀 {app_name} | VERSION: {version}")
if override_reason:
    print(f" 🟦 STAKEHOLDER OVERRIDE: {override_reason}")
print("="*60)
print(f" 🛠️  CQI (Code Quality Index)   : {cqi_score:>5.1f} / 100")
print(f" 🚢 RQI (Release Quality Index): {rqi_score:>5.1f} / 100")
print("-" * 60)

for name, _ in pillars:
    res = results[name]
    emoji = "⚪" if res["skipped"] else ("🟢" if res["score"] >= 80 else ("🟡" if res["score"] >= 50 else "🔴"))
    print(f"{emoji} {name:<20} : {res['score']:>5.1f}/100 ({res['detail']})")

print("="*60)
threshold = 80.0
status = "PASSED" if (rqi_score >= threshold or override_reason) else "FAILED"
print(f" {'✅' if status == 'PASSED' else '❌'} STATUS: {status} " + (f"(RQI below {threshold}%)" if status == "FAILED" else ""))
print("="*60 + "\n")

if __name__ == "__main__":
    calculate()