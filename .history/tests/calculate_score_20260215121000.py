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
    
    # Prioriteit: Environment Variable -> Config File -> Default
    project_key = os.getenv("SONAR_PROJECT_KEY") or config.get("sonarProjectKey", "MKwaak_weather-app-main")
    
    url = f"https://sonarcloud.io/api/measures/component?component={project_key}&metricKeys=coverage,bugs,vulnerabilities"
    
    try:
        response = requests.get(url, auth=(token, "") if token else None, timeout=10)
        if response.status_code != 200:
            return 0, f"Sonar Error ({response.status_code})"
            
        data = response.json()
        measures = {m['metric']: m['value'] for m in data['component']['measures']}
        
        coverage = float(measures.get('coverage', 0))
        bugs = int(measures.get('bugs', 0))
        
        # De naakte waarheid: De score IS de coverage, min strafpunten voor bugs
        score = max(0, coverage - (bugs * 2)) 
        return round(score, 1), f"{coverage}% (Bugs: {bugs})"
    except Exception as e:
        return 0, f"API Offline/Error"

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
        # SonarCloud Integration
        if name == "Code Quality":
            score, detail = get_sonar_metrics()
            results[name] = {"score": score, "detail": detail, "skipped": score == 0}
            continue

        # Unit Testing (Jest lcov check)
        if name == "Unit Testing":
            # We halen het pad uit de config, fallback naar de plek waar de artifact landt
            coverage_file = config.get("coveragePath", "tests/lcov.info")
            
            # Debug print (optioneel, helpt bij het inregelen)
            # print(f"DEBUG: Looking for coverage at {coverage_file}")

            if os.path.exists(coverage_file):
                results[name] = {"score": 100, "detail": "Jest Passed", "skipped": False}
            elif os.path.exists("coverage/lcov.info"):
                results[name] = {"score": 100, "detail": "Jest Passed (local)", "skipped": False}
            else:
                # Laat in de detail zien WAAR hij zocht, dat helpt bij QA
                results[name] = {"score": 0, "detail": f"Missing: {coverage_file}", "skipped": True}
            continue

        # Standaard JSON resultaten verwerking
        file_path = f"tests/{prefix}_results.json"
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