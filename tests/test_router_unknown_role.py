from core.router import route_task


def test_unknown_role_routes_to_dynamic_specialist():
    role, cls, model, out = route_task(
        {"id": "1", "role": "Alien", "title": "Alien", "description": "Explore"}
    )
    assert role == "Dynamic Specialist"
