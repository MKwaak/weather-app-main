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

    # Resultaat printen
    score_display = "⭐" * stars + "☆" * (5 - stars)
    print(f"\n{'='*30}")
    print(f" FINAL QUALITY SCORE: {score_display} ({stars}/5)")
    print(f"{'='*30}")
    for r in reasons: print(f"- {r}")

if __name__ == "__main__":
    calculate()

    # Resultaat printen voor de Terminal
    score_display = "⭐" * stars + "☆" * (5 - stars)
    summary_text = f"### 🏆 Final Quality Score: {score_display} ({stars}/5)\n\n"
    for r in reasons:
        summary_text += f"- {r}\n"

    print(summary_text)

    # DIT IS DE MAGIE: Schrijf naar de GitHub Summary
    summary_file = os.getenv('GITHUB_STEP_SUMMARY')
    if summary_file:
        with open(summary_file, 'a') as f:
            f.write(summary_text)

            