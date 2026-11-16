"""Тесты построения графа (BFS), фильтрации и поиска циклов."""

from graph import build_graph, find_cycles, format_graph

DIAMOND = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
CYCLES = {"A": ["B"], "B": ["C", "D"], "C": ["A"], "D": ["D"]}


def deps_of(repo):
    """Возвращает функцию зависимостей для словаря-репозитория."""
    return lambda name: repo.get(name, [])


def test_bfs_order_and_transitivity():
    """Граф содержит транзитивные зависимости в порядке BFS."""
    graph = build_graph("A", deps_of(DIAMOND))
    assert list(graph) == ["A", "B", "C", "D"]
    assert graph["C"] == ["D"]


def test_each_package_visited_once():
    """Общая зависимость запрашивается один раз."""
    calls = []

    def deps(name):
        """Запоминает запросы и возвращает зависимости."""
        calls.append(name)
        return DIAMOND[name]

    build_graph("A", deps)
    assert sorted(calls) == ["A", "B", "C", "D"]


def test_cycles_terminate():
    """Циклические зависимости не приводят к зацикливанию."""
    graph = build_graph("A", deps_of(CYCLES))
    assert graph == CYCLES


def test_no_recursion_on_long_chain():
    """Длинная цепочка обрабатывается без переполнения стека."""
    length = 5000
    chain = {f"P{i}": [f"P{i + 1}"] for i in range(length)}
    graph = build_graph("P0", deps_of(chain))
    assert len(graph) == length + 1
    assert find_cycles(graph, "P0") == []


def test_filter_excludes_packages():
    """Пакеты с подстрокой не учитываются, как и их зависимости."""
    graph = build_graph("A", deps_of(DIAMOND), exclude="B")
    assert graph == {"A": ["C"], "C": ["D"], "D": []}


def test_filter_excludes_root():
    """Если подстроку содержит сам пакет, граф пуст."""
    assert build_graph("A", deps_of(DIAMOND), exclude="A") == {}


def test_filter_breaks_cycle():
    """Фильтр может разорвать цикл."""
    graph = build_graph("A", deps_of(CYCLES), exclude="C")
    assert find_cycles(graph, "A") == [["D", "D"]]


def test_find_cycles():
    """Находятся все циклы, включая петлю."""
    cycles = find_cycles(CYCLES, "A")
    assert ["A", "B", "C", "A"] in cycles
    assert ["D", "D"] in cycles
    assert len(cycles) == 2


def test_no_cycles_in_diamond():
    """Ромб - не цикл."""
    assert find_cycles(DIAMOND, "A") == []
    assert find_cycles({}, "A") == []


def test_format_graph():
    """Строки «пакет -> зависимости»."""
    assert format_graph({"A": ["B", "C"], "B": []}) == [
        "  A -> B, C",
        "  B -> (нет)",
    ]
