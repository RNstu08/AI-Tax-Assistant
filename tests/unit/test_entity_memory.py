from app.nlu.context import EntityMemory


def test_memory_remembers_and_resolves():
    mem = EntityMemory()
    item = {"kind": "equipment_item", "data": {"description": "monitor"}}
    mem.remember(item)
    assert len(mem.entities) == 1

    resolved = mem.resolve("get another one of those", kind_hint="equipment_item")
    assert resolved is not None
    assert resolved["data"]["description"] == "monitor"
