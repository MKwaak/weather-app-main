import pytest
from playwright.sync_api import Page, expect

def test_entry_point_validation(page: Page):
    # TIP: Pas de poort aan naar de output van 'minikube service weather-service --url'
    url = "http://127.0.0.1:52428" 
    
    print(f"\nValidatie van entry point op: {url}")
    page.goto(url)
    
    # Check 1: Is de pagina geladen? (Zoekt naar de titel)
    expect(page).to_have_title("Weather Station Hub")
    
    # Check 2: Is de versie-indicator aanwezig?
    version_tag = page.locator("#version-tag")
    expect(version_tag).to_be_visible()
    
    # Check 3: Is de content dynamisch? (Zoekt naar de stad-input)
    search_input = page.locator("#city-input")
    expect(search_input).to_be_visible()
    
    versie = version_element = version_tag.inner_text()
    print(f"✅ Entry Test geslaagd voor versie: {versie}")