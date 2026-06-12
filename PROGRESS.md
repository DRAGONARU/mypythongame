# PROGRESS — Прогресс проекта

## Последняя проверка: 2026-06-12

---

## Инфраструктура

| Элемент | Статус | Примечание |
|---------|--------|------------|
| `pyproject.toml` | ✅ Готов | Имя, зависимости, pytest-конфиг, build-system |
| Структура папок `src/` | ✅ Создана | core, entities, systems, rendering, input, audio, ui, utils, world |
| `__init__.py` во всех пакетах | ✅ Готов | Все 9 пакетов + core/ecs |
| `tests/` | ⚠️ Пустая | Нет ни одного теста |
| `assets/` | ⚠️ Пустая | Нет ассетов |
| `config/` | ⚠️ Пустая | Нет конфигов |
| egg-info мусор | ✅ Игнорируется | `*.egg-info/` в .gitignore |

---

## Фаза 1 — Фундамент

### 1.1 Sparse Set ECS + Generation Handles

| Компонент | Статус | Примечание |
|-----------|--------|------------|
| `Entity` (id + generation) | ✅ Готов | frozen dataclass, slots, auto hash/eq, docstrings |
| `SparseSet[T]` | ✅ Готов | Generic[T], insert/remove/get/contains/len/iter/iter_with_entities, docstrings |
| `World` | ✅ Готов | create/destroy entity, add/get/remove component, query, _is_alive guard, docstrings |
| `Query` | ✅ Готов | lazy iterator, smallest-set optimisation, Entity в yield, type_to_index, guard на дубликаты, __repr__, docstrings |
| `System` (базовый класс) | ✅ Готов | ABC, abstractmethod update(world), docstrings |
| `__init__.py` реэкспорт | ❌ Не начат | Entity, SparseSet, World, Query, System — публичный API |
| Тесты на ECS | ❌ Не начат | entity, sparse_set, world, query, system |

### 1.2 Fixed Tick Game Loop

| Компонент | Статус |
|-----------|--------|
| `game_loop.py` | ⚠️ Файл есть, но пустой |
| Fixed tick (1/120 sec) | ❌ Не начат |
| Accumulator pattern | ❌ Не начат |
| Рендер с interpolation | ❌ Не начат |
| Тесты на детерминизм loop | ❌ Не начат |

### 1.3 Spatial Hash Grid

| Компонент | Статус |
|-----------|--------|
| `SpatialHash` | ❌ Не начат |
| insert / remove / query | ❌ Не начат |
| Тесты | ❌ Не начат |

---

## Фаза 2 — Движение + Время

| Компонент | Статус |
|-----------|--------|
| Event Log (с Undo) | ❌ |
| Ring Buffer Snapshots | ❌ |
| Rewind (reverse replay) | ❌ |
| Selective Rewind + TimelineLayer | ❌ |
| Time Domains (local_time_scale) | ❌ |
| Time Bubble | ❌ |

## Фаза 3 — Геймплей

| Компонент | Статус |
|-----------|--------|
| Knife System (3 типа MVP + 4 доп.) | ❌ |
| Spell Cards (event-driven, мана) | ❌ |
| Способности времени (мана времени) | ❌ |
| Enemy System | ❌ |
| Collision System | ❌ |
| Player (Сакуя: HP + Mana + TimeMana + Experience) | ❌ |
| Ввод / Управление | ❌ |
| Рендеринг | ❌ |
| Roguelike прогрессия (опыт, уровни, драфт) | ❌ |

## Фаза 4 — Продвинутые механики

| Компонент | Статус |
|-----------|--------|
| Rollback DSU | ❌ |
| Persistent Snapshots | ❌ |
| Sweep & Prune | ❌ |
| Timeline Fracture | ❌ (вне MVP) |

---

## Проблемы, требующие внимания

1. **Нет тестов** — нужно написать тесты на Entity, SparseSet, World, Query
2. **`game_loop.py` пустой** — следующий приоритет после ECS
3. **Docstring-несогласованность** — исправлено ✅

---

## Следующие шаги (по приоритету)

1. ~~Удалить мусор egg-info, переустановить пакет~~ ✅
2. ~~Добавить `__init__.py` во все пакеты `src/`~~ ✅
3. ~~Реализовать Entity + SparseSet~~ ✅
4. ~~Реализовать `World`~~ ✅
5. ~~Реализовать `Query`~~ ✅
6. ~~Исправить docstring-примеры~~ ✅
7. ~~Реализовать `System`~~ ✅
8. Обновить `__init__.py` в ecs — реэкспорт публичного API (Entity, SparseSet, World, Query, System)
9. Написать тесты на весь ECS (entity, sparse_set, world, query, system)
10. Реализовать Fixed Tick Game Loop (`src/core/game_loop.py`)
