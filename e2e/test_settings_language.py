def test_set_language_english(page, base_url):
    page.goto(f"{base_url}/?view=settings")
    page.get_by_text("Settings").wait_for()
    # Force English to stabilize text selectors
    page.get_by_label("Language").select_option("en")
    page.get_by_role("button", name="Apply language").click()
