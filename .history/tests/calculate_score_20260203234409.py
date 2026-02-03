import json
import os

def calculate():
    stars = 0
    reasons = []

    # 1. Entry Test (We gaan ervan uit dat als de pipeline hier is, deze geslaagd is)
    stars += 1
    reasons.append("Entry Test: PASSED")

    # 2. Check Performance Baseline
    try:
        with open(next(f for f in os.listdir('tests') if f.startswith('perf_')), 'r') as f:
            data = json.load(f)
            if data['metrics']['http_req_duration']['values']['p(95)'] < 200:
                stars += 1
                reasons.append("Performance: FAST (<200ms)")
    except: reasons.append("Performance: MISSING/FAILED")

    # 3. Check Load Test
    try:
        with open(next(f for f in os.listdir('tests') if f.startswith('load_')), 'r') as f:
            data = json.load(f)
            if data['metrics']['http_req_failed']['values']['rate'] == 0:
                stars += 1
                reasons.append("Load: STABLE (0% errors)")
    except: reasons.append("Load: MISSING/FAILED")

    # 4. Check Chaos Recovery
    try:
        with open(next(f for f in os.listdir('tests') if f.startswith('chaos_')), 'r') as f:
            data = json.load(f)
            if data['metrics']['http_req_failed']['values']['rate'] == 0:
                stars += 1
                reasons.append("Chaos: RESILIENT")
    except: reasons.append("Chaos: MISSING/FAILED")

    # 5. Completheid Check (zijn alle scripts aanwezig?)
    required_files = ['test_entry.py', 'performance_test.js', 'load_test.js']
    if all(os.path.exists(f"tests/{f}") for f in required_files):
        stars += 1
        reasons.append("Framework: COMPLETE")

    # 6. Security Scan Check
    try:
        with open('tests/security_results.json', 'r') as f:
            sec_data = json.load(f)
            # Check of er vulnerabilities zijn gevonden
            vulns = sec_data.get('Results', [{}])[0].get('Vulnerabilities', [])
            if len(vulns) == 0:
                stars += 1
                reasons.append("Security: CLEAN (No High/Critical CVEs)")
            else:
                reasons.append(f"Security: FAILED ({len(vulns)} vulnerabilities found)")
    except:
        reasons.append("Security: NOT SCANNED")

    # 1. Bepaal de score weergave (nu op basis van 6 sterren)
    total_stars = 6
    score_display = "⭐" * stars + "☆" * (total_stars - stars)
    
    # 2. Maak de tekst voor de Terminal
    terminal_output = f"\n{'='*40}\n"
    terminal_output += f" 🏆 FINAL QUALITY SCORE: {score_display} ({stars}/{total_stars})\n"
    terminal_output += f"{'='*40}\n"
    for r in reasons:
        terminal_output += f"- {r}\n"
    
    print(terminal_output)

    # 3. Maak de tekst voor de GitHub Step Summary (met Markdown)
    summary_text = f"### 🏆 Final Quality Score: {score_display} ({stars}/{total_stars})\n\n"
    summary_text += "| Check | Status |\n"
    summary_text += "| :--- | :--- |\n"
    for r in reasons:
        # Splitst de reden in Check en Status voor een mooie tabel
        parts = r.split(': ')
        check_name = parts[0]
        status = parts[1] if len(parts) > 1 else "OK"
        summary_text += f"| {check_name} | {status} |\n"

    # Schrijf naar de GitHub Summary file
    summary_file = os.getenv('GITHUB_STEP_SUMMARY')
    if summary_file:
        with open(summary_file, 'a') as f:
            f.write(summary_text)

if __name__ == "__main__":
    calculate()


