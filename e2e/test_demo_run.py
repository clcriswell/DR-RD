def test_demo_run_end_to_end(page, base_url):
    page.goto(f"{base_url}/")
    page.get_by_role("button", name="Run demo").click()
    # Expect quick completion and a Trace entrypoint
    page.get_by_text("Trace").wait_for(timeout=60_000)
    # Navigate to Trace page
    page.goto(f"{base_url}/?view=trace")
    page.get_by_text("Trace Viewer").wait_for()
    # Basic assertions: at least one step rendered
    assert page.locator("text=Step 1").first.is_visible()
