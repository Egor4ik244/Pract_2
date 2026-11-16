import json
from pathlib import Path
import shutil
import subprocess
import sys

def _node_label(node):
    """Возвращает подпись тестового или реального пакета."""
    if isinstance(node, tuple):
        package, version = node
        return f"{package} ({version})"

    return node


def to_dot(graph):
    """Преобразует граф зависимостей в описание Graphviz DOT."""
    node_ids = {
        node: f"node_{index}"
        for index, node in enumerate(graph)
    }

    lines = [
        "digraph dependencies {",
        '    node [shape="box"];'
    ]

    for node, node_id in node_ids.items():
        label = json.dumps(
            _node_label(node),
            ensure_ascii=False
        )
        lines.append(f"    {node_id} [label={label}];")

    for node, dependencies in graph.items():
        source = node_ids[node]

        for dependency in dependencies:
            target = node_ids[dependency]
            lines.append(f"    {source} -> {target};")


    lines.append("}")

    return "\n".join(lines) + "\n"


def render_graph(graph, output_prefix):
    """Сохраняет DOT и создаёт PNG, если установлен Graphviz."""
    prefix = Path(output_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)

    dot_path = Path(f"{prefix}.dot")
    image_path = Path(f"{prefix}.png")

    dot_path.write_text(to_dot(graph), encoding="utf-8")

    executable = shutil.which("dot")

    if executable is None:
        print(
            "Graphviz не найден. Установите его для создания PNG.",
            file=sys.stderr
        )
        return dot_path, None

    try:
        subprocess.run(
            [
                executable,
                "-Tpng",
                str(dot_path),
                "-o",
                str(image_path)
            ],
            capture_output=True,
            text=True,
            check=True
        )
    except subprocess.CalledProcessError as error:
        raise ValueError(
            f"Ошибка Graphviz: {error.stderr.strip()}"
        ) from error

    return dot_path, image_path


def open_image(image_path):
    """Открывает изображение стандартным приложением системы."""
    image_path = str(Path(image_path).resolve())

    if sys.platform == "darwin":
        command = ["open", image_path]
    elif sys.platform == "win32":
        import os

        os.startfile(image_path)
        return
    else:
        command = ["xdg-open", image_path]

    try:
        subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError(
            f"Не удалось открыть изображение: {error}"
        ) from error


def to_ascii(graph, root):
    """Возвращает ASCII-дерево с отметками повторных вершин."""
    lines = [_node_label(root)]
    expanded = {root}

    _append_ascii(
        graph,
        root,
        "",
        {root},
        expanded,
        lines
    )

    return "\n".join(lines)


def _append_ascii(graph, node, prefix, path, expanded, lines):
    """Добавляет ветви дерева, предотвращая повторный обход."""
    dependencies = graph.get(node, [])

    for index, dependency in enumerate(dependencies):
        is_last = index == len(dependencies) - 1
        connector = "`-- " if is_last else "|-- "
        label = _node_label(dependency)

        if dependency in path:
            lines.append(f"{prefix}{connector}{label} [cycle]")
            continue

        if dependency in expanded:
            lines.append(f"{prefix}{connector}{label} [seen]")
            continue

        lines.append(f"{prefix}{connector}{label}")
        expanded.add(dependency)

        next_prefix = prefix + ("    " if is_last else "|   ")

        _append_ascii(
            graph,
            dependency,
            next_prefix,
            path | {dependency},
            expanded,
            lines
        )
