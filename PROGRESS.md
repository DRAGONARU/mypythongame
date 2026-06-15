# PROGRESS — Прогресс проекта

## Последняя проверка: 2026-06-15

---

## Инфраструктура

| Элемент | Статус | Примечание |
|---------|--------|------------|
| `pyproject.toml` | ✅ Готов | Имя, зависимости, pytest-конфиг, build-system |
| Структура папок `src/` | ✅ Создана | core, entities, systems, rendering, input, audio, ui, utils, world |
| `__init__.py` во всех пакетах | ✅ Готов | Все 9 пакетов + core/ecs |
| `tests/` | ✅ 143 теста | entity(8), sparse_set(22), world(35), query(20), system(10), game_loop(11), spatial_hash(29) — все проходят |
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
| `__init__.py` реэкспорт | ✅ Готов | Entity, SparseSet, World, Query, System — публичный API |
| Тесты на ECS | ✅ Готов | 103 теста, все проходят |

### 1.2 Fixed Tick Game Loop

| Компонент | Статус |
|-----------|--------|
| `game_loop.py` | ✅ Готов | Fixed tick 1/120 Hz, accumulator, spiral-of-death guard, interpolation alpha |
| `__init__.py` реэкспорт | ✅ Готов | GameLoop экспортирован из src.core |
| Fixed tick (1/120 sec) | ✅ Готов | GameLoop.FIXED_DT = 1/120 |
| Accumulator pattern | ✅ Готов | Накопление real_dt, потребление FIXED_DT чанками |
| Рендер с interpolation | ✅ Готов | alpha = accumulator / FIXED_DT → render_fn(alpha) |
| Spiral-of-death guard | ✅ Готов | MAX_TICKS_PER_FRAME=5, reset accumulator |
| Тесты на GameLoop | ✅ Готов | 11 тестов: start/stop, tick counter, alpha, spiral-of-death, real_dt cap |

### 1.3 Spatial Hash Grid

| Компонент | Статус | Примечание |
|-----------|--------|------------|
| `SpatialHashGrid` | ✅ Готов | insert/remove/update/query_circle/query_rect/clear, docstrings |
| Broad-phase only | ✅ Готов | query-методы возвращают кандидатов, narrow-phase — ответственность CollisionSystem |
| `__init__.py` реэкспорт | ✅ Готов | SpatialHashGrid экспортирован из src.utils |
| Тесты | ✅ Готов | 29 тестов: все методы + интеграционный тест |

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

1. **Нет тестов** — ✅ исправлено (143 теста)
2. **`game_loop.py` пустой** — ✅ исправлено
3. **`spatial_hash.py` пустой** — ✅ исправлено
4. **Docstring-несогласованность** — ✅ исправлено
5. **`__init__.py` в utils** — ✅ исправлено (SpatialHashGrid экспортирован)

---

## Следующие шаги (по приоритету)

1. ~~Удалить мусор egg-info, переустановить пакет~~ ✅
2. ~~Добавить `__init__.py` во все пакеты `src/`~~ ✅
3. ~~Реализовать Entity + SparseSet~~ ✅
4. ~~Реализовать `World`~~ ✅
5. ~~Реализовать `Query`~~ ✅
6. ~~Исправить docstring-примеры~~ ✅
7. ~~Реализовать `System`~~ ✅
8. ~~Написать тесты на весь ECS~~ ✅ (103 теста)
9. ~~Обновить `__init__.py` в ecs — реэкспорт публичного API~~ ✅
10. ~~Реализовать Fixed Tick Game Loop (`src/core/game_loop.py`)~~ ✅
11. ~~Написать тесты на GameLoop (детерминизм, accumulator, spiral of death, stop)~~ ✅ (11 тестов)
12. ~~Реализовать Spatial Hash Grid (`src/utils/spatial_hash.py`)~~ ✅ (29 тестов)
13. ~~Экспортировать SpatialHashGrid из `src/utils/__init__.py`~~ ✅
14. Реализовать компоненты (Position, Velocity, Collider, Health, Mana, TimeMana, Experience)
15. Реализовать MovementSystem
