import requests
import json
import argparse

def run_location_test(url):
    # De 'Blacklist' van lastige locaties
    test_cases = [
        {"city": "Athens", "expected_country": "GR"},
        {"city": "Oslo", "expected_country": "NO"},
        {"city": "London", "expected_country": "GB"}
    ]
    
    results = {
        "test_name": "Location Accuracy & Mapping",
        "scenarios": [],
        "score": 100
    }

    print(f"🌍 Start Locatie-test op: {url}")

    for case in test_cases:
        city = case["city"]
        try:
            response = requests.get(f"{url}/weather?city={city}", timeout=5)
            data = response.json()
            
            # Check de country code in de response
            received_country = data.get('sys', {}).get('country', 'UNKNOWN')
            
            status = "PASS" if received_country == case["expected_country"] else "FAIL"
            
            results["scenarios"].append({
                "input": city,
                "expected": case["expected_country"],
                "received": received_country,
                "status": status
            })

            if status == "FAIL":
                results["score"] -= 20 # Strafpunten per foute mapping
                print(f"❌ FOUT: {city} gaf {received_country}, verwachtte {case['expected_country']}")

        except Exception as e:
            print(f"⚠️ Kon {city} niet testen: {e}")
            results["score"] -= 10

    # Score kan niet onder 0
    results["score"] = max(0, results["score"])

    # Schrijf weg naar de root voor de Judge
    with open('functional_results.json', 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    args = parser.parse_args()
    run_location_test(args.url)