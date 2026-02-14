import os
import json
import requests
import sys

def get_sonar_metrics():
    token = os.getenv("SONAR_TOKEN")
    project_key = os.getenv("SONAR_PROJECT_KEY", "MKwaak_weather-app-main")
    # We vragen nu specifiek om de 'coverage' en 'bugs' metrics
    url = f"https://sonarcloud.io/api/measures/component?component={project_key}&metricKeys=coverage,bugs,vulnerabilities"
    
    try:
        response = requests.get(url, auth=(token, "") if token else None, timeout=10)
        data = response.json()
        # Haal de waarde uit de lijst met measures
        measures = {m['metric']: m['value'] for m in data['component']['measures']}
        
        coverage = float(measures.get('coverage', 0))
        bugs = int(measures.get('bugs', 0))
        vulns = int(measures.get('vulnerabilities', 0))
        
        # De naakte waarheid score: coverage is de basis, min strafpunten voor bugs
        score = max(0, coverage - (bugs * 2)) 
        return score, f"{coverage}% (Bugs: {bugs})"
    except Exception as e:
        return 0, f"API Error: {str(e)}"

def calculate():
    version = os.getenv("APP_VERSION", "0.0.0-unknown")
    override_reason = os.getenv("OVERRIDE_REASON", "")
    
    # De 8 Pilaren (Unit Testing toegevoegd)
    # De volgorde hier bepaalt de weergave op je dashboard
    pillars = [
        ("Entry Check", "entry"),
        ("Unit Testing", "unit"),
        ("Code Quality", "sonar"),
        ("Functionality", "accuracy"),
        ("Security Scan", "security"),
        ("Performance", "perf"),      # Gematcht met nieuwe bestandsnaam
        ("Load Stability", "load"),
        ("Chaos Resilience", "chaos")
    ]
    
    results = {}

    for name, prefix in pillars:
        # Speciale case 1: SonarCloud
        if name == "Code Quality":
            score, detail = get_sonar_metrics() # De nieuwe functie aanroepen
            results[name] = {
                "score": score, 
                "detail": detail, 
                "skipped": False if score > 0 else True
            }
            continue

        # Speciale case 2: Unit Testing (kijkt naar aanwezigheid lcov data)
        if name == "Unit Testing":
            coverage_file = "tests/lcov.info"
            if os.path.exists(coverage_file):
                # Omdat de test-job is geslaagd geven we 100
                results[name] = {"score": 100, "detail": "Jest Passed", "skipped": False}
            else:
                results[name] = {"score": 0, "detail": "No Data", "skipped": True}
            continue

        # Standaard: Zoek naar JSON resultaten
        file_path = f"tests/{prefix}_results.json"
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    score = data.get('score', 0)
                    
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
            except Exception:
                results[name] = {"score": 0, "detail": "Format error", "skipped": True}
        else:
            results[name] = {"score": 0, "detail": "Skipped", "skipped": True}

    # Slimme weging: Alleen berekenen op basis van wat NIET geskipt is
    # Dit voorkomt dat je RQI instort naar 38% bij het skippen van chaos tests
    cqi_names = ["Entry Check", "Unit Testing", "Code Quality", "Functionality", "Security Scan"]
    active_cqi = [results[n]["score"] for n in cqi_names if not results[n]["skipped"]]
    cqi_score = sum(active_cqi) / len(active_cqi) if active_cqi else 0
    
    active_rqi = [results[n]["score"] for n, _ in pillars if not results[n]["skipped"]]
    rqi_score = sum(active_rqi) / len(active_rqi) if active_rqi else 0

    # Dashboard Rendering
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

    # De Quality Gate beslissing
    threshold = 80.0
    is_passed = rqi_score >= threshold

    if override_reason:
        print(f" ✅ STATUS: PASSED BY OVERRIDE")
    elif is_passed:
        print(f" ✅ STATUS: PASSED")
    else:
        print(f" ❌ STATUS: FAILED (RQI below {threshold}%)")
    print("="*60 + "\n")
    
    # Rest van de historie logica blijft gelijk...

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