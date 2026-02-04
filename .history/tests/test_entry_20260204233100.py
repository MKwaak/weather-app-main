import os
import pytest
from playwright.sync_api import Page, expect

def test_entry_point_validation(page: Page):
    # Hij pakt nu TEST_URL uit de GitHub Action, of valt terug op 8080 als je lokaal test
    url = os.getenv('TEST_URL', 'http://localhost:8080')
    
    print(f"\nValidatie op: {url}")
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