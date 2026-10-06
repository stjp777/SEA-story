"""Run: python test_app.py   (live LLM test runs only if Ollama is up)"""
import itertools
import json
import random
import urllib.request

import app

data = json.loads((app.HERE / "data.json").read_text())


def stories():
    """A sample of mixed preset combos + one fully custom story."""
    combos = list(itertools.product(data["main_characters"], data["reveals"], data["plots"], data["themes"]))
    random.seed(1)
    for mc, rv, pl, th in random.sample(combos, 10):
        s1, s2 = random.sample(data["supporting_characters"], 2)
        yield dict(main_character=mc, reveal=rv, supporting_1=s1, supporting_2=s2, plot=pl, theme=th)
    yield dict(main_character="Zed", reveal="can hear the dead", supporting_1="Ana", supporting_2="Bo",
               plot="a lighthouse keeper's last night", theme="grief")


def test_prompt_contains_all_inputs():
    for s in stories():
        p = app.build_prompt(s)
        for k in app.FIELDS:
            assert s[k] in p, (k, s[k])


def test_validate():
    good = {"title": "t", "scenes": [{"title": "a", "description": "b"}],
            "ending": {"description": "d", "reveal": "r", "cliffhanger": "c"}}
    assert app.validate(good) is None
    assert app.validate([]) == "not an object"
    assert app.validate({**good, "scenes": []}) == "no scenes"
    assert app.validate({**good, "scenes": [{"title": "a"}]})
    assert app.validate({**good, "ending": {"description": "d", "reveal": " ", "cliffhanger": "c"}})
    assert app.validate({**good, "ending": None})


def test_live():
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
    except OSError:
        print("  (skipped: Ollama not running)")
        return
    s = next(stories())
    b = app.generate(s)
    assert app.validate(b) is None
    print(f"  live OK: {len(b['scenes'])} scenes | reveal: {b['ending']['reveal'][:100]}")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
