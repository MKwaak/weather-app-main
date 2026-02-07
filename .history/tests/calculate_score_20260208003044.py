import glob
import os
import json

def calculate():
    scores = {}
    details = []

    def get_latest_data(prefix):
        file_path = f"tests/{prefix}_results.json"
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return None

    # 1. Performance Score (Baseline)
    # Target: < 200ms is 100 punten. Elke 10ms daarboven is -1 punt.
    perf_data = get_latest_data('perf')
    if perf_data:
        p95 = perf_data['metrics']['http_req_duration']['values']['p(95)']
        if p95 <= 200:
            p_score = 100
        else:
            p_score = max(0, 100 - int((p95 - 200) / 10))
        scores['Performance'] = p_score
        details.append(f"Performance Index: {p_score}/100 (Latency: {p95:.2f}ms)")
    else:
        scores['Performance'] = 0
        details.append("Performance: No data found (0/100)")

    # 2. Load Stability Score
    # Lineair: 100% succes = 100 punten. 98% succes = 98 punten.
    load_data = get_latest_data('load')
    if load_data:
        fail_rate = load_data['metrics']['http_req_failed']['values']['rate']
        l_score = int((1.0 - fail_rate) * 100)
        scores['Load'] = l_score
        details.append(f"Load Stability Index: {l_score}/100 (Success Rate: {(1.0-fail_rate)*100:.2f}%)")
    else:
        scores['Load'] = 0
        details.append("Load: No data found (0/100)")

    # 3. Chaos Resilience Score
    # Lineair: Hoeveel procent van de requests overleefde de pod-delete?
    chaos_data = get_latest_data('chaos')
    if chaos_data:
        fail_rate = chaos_data['metrics']['http_req_failed']['values']['rate']
        c_score = int((1.0 - fail_rate) * 100)
        scores['Chaos'] = c_score
        details.append(f"Chaos Resilience Index: {c_score}/100 (Availability: {(1.0-fail_rate)*100:.2f}%)")
    else:
        scores['Chaos'] = 0
        details.append("Chaos: No data found (0/100)")

    # 4. Security Score
    # 0 vulns = 100 punten. Elke vuln is -10 punten.
    try:
        with open('tests/security_results.json', 'r') as f:
            sec_data = json.load(f)
            vulns = len(sec_data.get('Results', [{}])[0].get('Vulnerabilities', []))
            s_score = max(0, 100 - (vulns * 10))
            scores['Security'] = s_score
            details.append(f"Security Index: {s_score}/100 ({vulns} vulnerabilities)")
    except:
        scores['Security'] = 0
        details.append("Security: Not scanned (0/100)")

    # Gemiddelde berekenen
    final_index = sum(scores.values()) / len(scores)

    # --- OUTPUT ---
    print("\n" + "="*45)
    print(f" 🏆 WEATHER APP QUALITY DASHBOARD")
    print("="*45)
    for d in details:
        print(f"- {d}")
    print("-" * 45)
    print(f" FINAL QUALITY INDEX: {final_index:.1f} / 100")
    print("="*45 + "\n")

    # GitHub Step Summary (Mooie tabel voor in de UI)
    summary_file = os.getenv('GITHUB_STEP_SUMMARY')
    if summary_file:
        with open(summary_file, 'a') as f:
            f.write(f"## 🏆 Quality Dashboard (Run {os.getenv('GITHUB_RUN_NUMBER')})\n")
            f.write(f"### **Final Quality Index: {final_index:.1f} / 100**\n\n")
            f.write("| Pillar | Score | Details |\n")
            f.write("| :--- | :--- | :--- |\n")
            for pillar, score in scores.items():
                detail_text = [d for d in details if pillar in d][0]
                status_emoji = "🟢" if score > 90 else "🟡" if score > 70 else "🔴"
                f.write(f"| {status_emoji} {pillar} | **{score}** | {detail_text.split(': ')[1]} |\n")

if __name__ == "__main__":
    calculate()