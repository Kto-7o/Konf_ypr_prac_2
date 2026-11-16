"""Построение графа зависимостей и операции над ним.

Граф строится обходом в ширину (BFS) без рекурсии с учетом
транзитивных зависимостей. Повторно встреченные пакеты в очередь не
добавляются, поэтому циклические зависимости не приводят к
зацикливанию; сами циклы находятся итеративным обходом в глубину.
Тот же обход строит граф обратных зависимостей, если вместо функции
прямых зависимостей передать функцию, возвращающую зависящие пакеты.
"""

from collections import deque
from typing import Callable, Dict, List

Graph = Dict[str, List[str]]
DependenciesFunc = Callable[[str], List[str]]

IN_PROGRESS = "in_progress"
DONE = "done"


def is_excluded(name: str, exclude: str) -> bool:
    """Проверяет, исключен ли пакет фильтром (пустой фильтр - нет)."""
    return bool(exclude) and exclude in name


def build_graph(root: str, dependencies: DependenciesFunc,
                exclude: str = "") -> Graph:
    """Строит граф зависимостей обходом в ширину без рекурсии.

    Args:
        root: анализируемый пакет.
        dependencies: функция, возвращающая прямые зависимости пакета.
        exclude: пакеты, имя которых содержит эту подстроку, не
            учитываются.

    Returns:
        Словарь «пакет -> список прямых зависимостей» в порядке обхода;
        пустой, если исключен сам анализируемый пакет.
    """
    if is_excluded(root, exclude):
        return {}
    graph: Graph = {}
    queue = deque([root])
    seen = {root}
    while queue:
        name = queue.popleft()
        children = [
            child for child in dependencies(name)
            if not is_excluded(child, exclude)
        ]
        graph[name] = children
        for child in children:
            if child not in seen:
                seen.add(child)
                queue.append(child)
    return graph


def find_cycles(graph: Graph, root: str) -> List[List[str]]:
    """Находит циклические зависимости итеративным обходом в глубину.

    Returns:
        Список циклов; цикл - путь, начинающийся и оканчивающийся
        одним пакетом, например ['A', 'B', 'A'].
    """
    if root not in graph:
        return []
    cycles = []
    state = {root: IN_PROGRESS}
    path = [root]
    stack = [iter(graph[root])]
    while stack:
        child = next(stack[-1], None)
        if child is None:
            stack.pop()
            state[path.pop()] = DONE
        elif state.get(child) == IN_PROGRESS:
            cycles.append(path[path.index(child):] + [child])
        elif child not in state:
            state[child] = IN_PROGRESS
            path.append(child)
            stack.append(iter(graph.get(child, [])))
    return cycles


def format_graph(graph: Graph, arrow: str = "->") -> List[str]:
    """Формирует строки «пакет -> зависимости» в порядке обхода.

    Для графа обратных зависимостей используется стрелка «<-».
    """
    return [
        f"  {name} {arrow} {', '.join(children) or '(нет)'}"
        for name, children in graph.items()
    ]
