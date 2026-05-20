# PROGRESS — Прогресс проекта

## Последняя проверка: 2026-05-20

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
| `Entity` (id + generation) | ✅ Готов | frozen dataclass, slots, auto hash/eq |
| `SparseSet[T]` | ✅ Готов | Generic[T], insert/remove/get/contains/len/iter/iter_with_entities |
| `World` (контейнер entities + components) | ❌ Не начат | Следующий шаг |
| `System` (базовый класс) | ❌ Не начат | |
| `Query` (итерация по компонентам) | ❌ Не начат | |
| Тесты на ECS | ❌ Не начат | |

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
| Event Log | ❌ |
| Ring Buffer Snapshots | ❌ |
| Rewind (полный) | ❌ |
| Selective Rewind + TimelineLayer | ❌ |
| Time Domains (local_time_scale) | ❌ |
| Time Bubble | ❌ |

## Фаза 3 — Геймплей

| Компонент | Статус |
|-----------|--------|
| Knife System (7 типов) | ❌ |
| Spell Cards (event-driven) | ❌ |
| Enemy System | ❌ |
| Collision System | ❌ |
| Player (Сакуя) | ❌ |
| Ввод / Управление | ❌ |
| Рендеринг | ❌ |

## Фаза 4 — Продвинутые механики

| Компонент | Статус |
|-----------|--------|
| Timeline Fracture | ❌ |
| Recursive Knife | ❌ |
| Zobrist Hash / State dedup | ❌ |
| Roguelike (прогрессия, уровни) | ❌ |

---

## Проблемы, требующие внимания

1. **Нет тестов** — нужно написать тесты на Entity и SparseSet параллельно с World
2. **`game_loop.py` пустой** — после завершения ECS
3. **Мелкие замечания SparseSet** — `Iterator` из typing (лучше из collections.abc), пробелы в keyword args (PEP 8)

---

## Следующие шаги (по приоритету)

1. ~~Удалить мусор egg-info, переустановить пакет~~ ✅
2. ~~Добавить `__init__.py` во все пакеты `src/`~~ ✅
3. ~~Реализовать Entity + SparseSet~~ ✅
4. **Реализовать `World`** (`src/core/ecs/world.py`) — текущий приоритет
5. Реализовать `Query` (`src/core/ecs/query.py`)
6. Реализовать `System` (`src/core/ecs/system.py`)
7. Обновить `__init__.py` в ecs — реэкспорт публичного API
8. Написать тесты на весь ECS (entity, sparse_set, world, query)
9. Реализовать Fixed Tick Game Loop (`src/core/game_loop.py`)
