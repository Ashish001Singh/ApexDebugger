from src.apex_copilot.rules.nested_loop import check_nested_loop

def test_single_loop_clean():
    code = "for (Id i : a) { System.debug(i); }"
    assert check_nested_loop(code) == []

def test_double_nested_flags_level2():
    code = "for (Id i : a) {\n  for (Id j : b) {\n    System.debug(j);\n  }\n}"
    rules = [f.rule.value for f in check_nested_loop(code)]
    assert "nested_loop_2" in rules
    assert "nested_loop_deep" not in rules

def test_triple_nested_flags_both():
    code = "for (Id i : a) {\n for (Id j : b) {\n  for (Id k : c) {\n   System.debug(k);\n  }\n }\n}"
    rules = [f.rule.value for f in check_nested_loop(code)]
    assert "nested_loop_2" in rules
    assert "nested_loop_deep" in rules