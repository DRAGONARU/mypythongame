# PROGRESS — Прогресс проекта

## Последняя проверка: 2026-06-20

---

## Инфраструктура

| Элемент | Статус | Примечание |
|---------|--------|------------|
| `pyproject.toml` | ✅ Готов | Имя, зависимости, pytest-конфиг, build-system |
| Структура папок `src/` | ✅ Создана | core, entities, systems, rendering, input, audio, ui, utils, world |
| `__init__.py` во всех пакетах | ✅ Готов | Все 9 пакетов + core/ecs |
| `tests/` | ✅ 230 тестов | entity(8), sparse_set(22), world(35), query(20), system(10), game_loop(11), spatial_hash(29), movement(7), input(5), collision(11), lifetime(8), combat(10), game(10), knife(27) — все проходят |
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

## Компоненты

| Компонент | Статус | Поля |
|-----------|--------|------|
| Position | ✅ | x, y |
| Velocity | ✅ | x, y |
| Collider | ✅ | radius |
| Health | ✅ | value, max_value |
| Mana | ✅ | value, max_value |
| TimeMana | ✅ | value, max_value |
| Experience | ✅ | level, current, to_next |
| TimeAffected | ✅ | scale |
| Owner | ✅ | entity |
| Lifetime | ✅ | remaining_ticks |
| Knife | ✅ | knife_type, damage, speed |
| Reflective | ✅ | bounces_remaining |
| Delayed | ✅ | activate_ticks |
| Player | ✅ | (маркер) |
| Enemy | ✅ | enemy_type, ai_state |
| CollisionFilter | ✅ | layer, mask |
| InputState | ✅ | mouse_x, mouse_y, mouse_pressed, keys_pressed |
| KnifeLoadout | ✅ | current, available, cooldown |
| Boss | ❌ | phase |
| Sprite | ❌ | texture_id, layer |
| Animation | ❌ | current_frame, frame_timer |
| TimelineAnchor | ❌ | timeline_id |
| Frozen | ❌ | remaining_ticks |
| SpellCard | ❌ | spell_type, remaining_ticks, cooldown |
| TimeBubble | ❌ | center_x, center_y, radius, scale, falloff |
| Projectile | ❌ | damage, owner_id |

---

## Системы

| Система | Статус | Тесты |
|---------|--------|-------|
| MovementSystem | ✅ Готов | 7 тестов |
| InputSystem | ✅ Готов | 5 тестов (пишет InputState в World) |
| CollisionSystem | ✅ Готов | 11 тестов (broad+narrow + CollisionFilter + CollisionEvent) |
| LifetimeSystem | ✅ Готов | 8 тестов |
| CombatSystem | ✅ Готов | 10 тестов (урон, уничтожение, friendly fire, reflective) |
| KnifeSystem | ✅ Готов | 27 тестов (спавн 3 типа, delayed, reflective bounce, selection) |
| EnemySystem | ❌ | — |
| TimeSystem | ❌ | — |

---

## Класс Game

| Элемент | Статус | Примечание |
|---------|--------|------------|
| `Game.__init__` | ✅ Готов | World + 6 систем + GameLoop |
| `_tick(dt)` | ✅ Готов | Инкремент tick, запуск систем, очистка events |
| `_render(alpha)` | ✅ Готов | Заглушка (pass) |
| `run()` / `stop()` | ✅ Готов | Делегирует в GameLoop |
| Порядок систем | ✅ | Input → Knife → Movement → Collision → Combat → Lifetime |

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
| Knife System (3 типа MVP + 4 доп.) | ✅ 3 типа MVP: Normal, Delayed, Reflective |
| Spell Cards (event-driven, мана) | ❌ |
| Способности времени (мана времени) | ❌ |
| Enemy System | ❌ |
| Collision System | ✅ Готов | broad+narrow + CollisionFilter (битовые слои) + CollisionEvent |
| Player (Сакуя: HP + Mana + TimeMana + Experience) | ⚠️ Компоненты готовы, нет спавна |
| Ввод / Управление | ✅ Готов | InputSystem: mouse + keyboard → InputState компонент |
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

1. **Нет тестов** — ✅ исправлено (230 тестов)
2. **`game_loop.py` пустой** — ✅ исправлено
3. **`spatial_hash.py` пустой** — ✅ исправлено
4. **Docstring-несогласованность** — ✅ исправлено
5. **`__init__.py` в utils** — ✅ исправлено (SpatialHashGrid экспортирован)
6. **`CollisionSystem._handle_collision`** — ✅ исправлено (генерирует CollisionEvent)
7. **`World._is_alive` приватный** — тесты используют приватный API
8. **`Game._render` — заглушка** — нет рендеринга
9. **Нет спавна игрока/врагов** — компоненты готовы, нет setup-функции

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
11. ~~Написать тесты на GameLoop~~ ✅ (11 тестов)
12. ~~Реализовать Spatial Hash Grid~~ ✅ (29 тестов)
13. ~~Экспортировать SpatialHashGrid~~ ✅
14. ~~Реализовать компоненты~~ ✅ (16 компонентов)
15. ~~Реализовать MovementSystem~~ ✅ (7 тестов)
16. ~~Реализовать InputSystem~~ ✅ (5 тестов)
17. ~~Реализовать CollisionSystem~~ ✅ (11 тестов)
18. ~~Реализовать LifetimeSystem~~ ✅ (8 тестов)
19. ~~Реализовать CombatSystem~~ ✅ (10 тестов)
20. ~~Реализовать KnifeSystem~~ ✅ (27 тестов, 3 типа ножей)
21. ~~Реализовать Game~~ ✅ (10 тестов)
22. Реализовать базовый рендеринг (Pygame: круги для Position + Collider)
23. Реализовать спавн игрока и врагов (тестовая арена)
24. Реализовать EnemySystem (ИИ: преследование игрока)
25. Реализовать TimeSystem (local_time_scale, Time Stop, Slow)
