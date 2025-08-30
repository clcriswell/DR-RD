def test_command_palette_open_and_navigate(page, base_url):
    page.goto(f"{base_url}/?cmd=1")
    page.get_by_text("Command palette").wait_for()
    # Search for Trace
    page.get_by_role("textbox").fill("Trace")
    # Select first result
    page.get_by_role("button", name="Select").first.click()
    # Should navigate or set params to Trace
    page.wait_for_url("**view=trace**")
