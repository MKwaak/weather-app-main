import glob
import os
import json

def calculate():
    stars = 0
    reasons = []

    # Helper functie om het nieuwste bestand te vinden
    def get_latest_data(prefix):
        # Zoek in de 'tests' map naar bestanden die beginnen met de prefix en eindigen op .json
        files = glob.glob(f"tests/{prefix}_*.json")
        if not files:
            return None
        # Pak het bestand met de meest recente wijzigingstijd
        latest_file = max(files, key=os.path.getmtime)
        try:
            with open(latest_file, 'r') as f:
                return json.load(f)
        except:
            return None

    # 1. Entry Test
    stars += 1
    reasons.append("Entry Test: PASSED")

    # 2. Check Performance Baseline
    metrics = data.get('metrics', {})
    duration = metrics.get('http_req_duration', {})

    # Check of 'values' bestaat, anders direct in de duration kijken
    if 'values' in duration:
            p95 = duration['values'].get('p(95)', 0)
    else:
            p95 = duration.get('p(95)', 0)

        print(f"Gevonden p95: {p95}")

    # 3. Check Load Test
    data = get_latest_data('load')
    if data and 'metrics' in data:
        metrics = data.get('metrics', {})
        failed = metrics.get('http_req_failed', {})
        # Pak 'rate' uit 'values' OF direct uit failed
        values = failed.get('values', failed)
        fail_rate = values.get('rate', 1.0) # 1.0 (100% fail) als fallback
        
        if fail_rate == 0:
            stars += 1
            reasons.append("Load: STABLE (0% errors)")
        else:
            reasons.append(f"Load: UNSTABLE ({fail_rate*100:.1f}% errors)")
    else: 
        reasons.append("Load: MISSING/FAILED")

    # 4. Check Chaos Recovery
    data = get_latest_data('chaos')
    if data and 'metrics' in data:
        metrics = data.get('metrics', {})
        failed = metrics.get('http_req_failed', {})
        # Pak 'rate' uit 'values' OF direct uit failed
        values = failed.get('values', failed)
        fail_rate = values.get('rate', 1.0)
        
        if fail_rate == 0:
            stars += 1
            reasons.append("Chaos: RESILIENT (Survived pod delete)")
        else:
            reasons.append(f"Chaos: FAILED (Downtime detected)")
    else: 
        reasons.append("Chaos: MISSING/FAILED")

    # 5. Completheid Check (zijn alle scripts aanwezig?)
    required_files = ['test_entry.py', 'performance_test.js', 'load_test.js']
    if all(os.path.exists(f"tests/{f}") for f in required_files):
        stars += 1
        reasons.append("Framework: COMPLETE")
    else:
        reasons.append("Framework: INCOMPLETE (Missing scripts)")

    # 6. Security Scan Check
    try:
        # Let op: zorg dat trivy output echt naar tests/security_results.json gaat
        with open('tests/security_results.json', 'r') as f:
            sec_data = json.load(f)
            vulns = sec_data.get('Results', [{}])[0].get('Vulnerabilities', [])
            if len(vulns) == 0:
                stars += 1
                reasons.append("Security: CLEAN")
            else:
                reasons.append(f"Security: FAILED ({len(vulns)} vulnerabilities)")
    except:
        reasons.append("Security: NOT SCANNED")

    # --- De rest van je weergave logica blijft hetzelfde ---
    total_stars = 6
    score_display = "⭐" * stars + "☆" * (total_stars - stars)
    
    terminal_output = f"\n{'='*40}\n"
    terminal_output += f" 🏆 FINAL QUALITY SCORE: {score_display} ({stars}/{total_stars})\n"
    terminal_output += f"{'='*40}\n"
    for r in reasons:
        terminal_output += f"- {r}\n"
    print(terminal_output)

    summary_file = os.getenv('GITHUB_STEP_SUMMARY')
    if summary_file:
        summary_text = f"### 🏆 Final Quality Score: {score_display} ({stars}/{total_stars})\n\n"
        summary_text += "| Check | Status |\n| :--- | :--- |\n"
        for r in reasons:
            parts = r.split(': ')
            summary_text += f"| {parts[0]} | {parts[1] if len(parts) > 1 else 'OK'} |\n"
        with open(summary_file, 'a') as f:
            f.write(summary_text)

if __name__ == "__main__":
    calculate()