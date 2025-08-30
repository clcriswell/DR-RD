def test_skip_link_and_focus(page, base_url):
    page.goto(f"{base_url}/")
    page.keyboard.press("Tab")
    page.get_by_role("link", name="Skip to main content").press("Enter")
    main = page.locator("#main")
    assert main.is_visible()
    snapshot = page.accessibility.snapshot()
    names = [node.get("name", "") for node in snapshot.get("children", [])]
    assert any("Start run" in n or "Run demo" in n for n in names)
