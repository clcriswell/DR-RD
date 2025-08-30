def test_reports_exports_visible(page, base_url):
    page.goto(f"{base_url}/?view=reports")
    page.get_by_text("Reports & Exports").wait_for()
    page.get_by_role("button", name="Download report (.md)").wait_for()
    page.get_by_role("button", name="Download report (.html)").wait_for()
    page.get_by_role("button", name="Download artifact bundle (.zip)").wait_for()
