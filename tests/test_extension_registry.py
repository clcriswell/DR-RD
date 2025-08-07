from dr_rd.extensions.registry import Registry


class Dummy:
    pass


def test_registry_add_get_list():
    reg = Registry()
    reg.register("dummy", Dummy)
    assert reg.get("dummy") is Dummy
    assert "dummy" in reg.list()
