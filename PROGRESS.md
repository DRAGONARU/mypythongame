# PROGRESS — Прогресс проекта

## Последняя проверка: 2026-06-21

---

## Инфраструктура

| Элемент | Статус | Примечание |
|---------|--------|------------|
| `pyproject.toml` | ✅ Готов | Имя, зависимости, pytest-конфиг, build-system |
| Структура папок `src/` | ✅ Создана | core, entities, systems, rendering, input, audio, ui, utils, world |
| `__init__.py` во всех пакетах | ✅ Готов | Все 9 пакетов + core/ecs |
| `tests/` | ✅ 340 тестов | entity(8), sparse_set(22), world(35), query(20), system(10), game_loop(11), spatial_hash(29), movement(7), player_movement(13), input(5), collision(11), lifetime(8), combat(10), game(11), knife(30), enemy(16), separation(13), snapshots(24), event_log(28), rewind(14) — все проходят |
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
| MovementSystem | ✅ Готов | 7 тестов (velocity × TimeAffected.scale per-tick) |
| PlayerMovementSystem | ✅ Готов | 13 тестов (WASD, диагональ-нормализация, in-place) |
| InputSystem | ✅ Готов | 5 тестов (пишет InputState в World) |
| CollisionSystem | ✅ Готов | 11 тестов (broad+narrow + CollisionFilter + CollisionEvent) |
| SeparationSystem | ✅ Готов | 13 тестов (анти-стак врагов, свой grid) |
| LifetimeSystem | ✅ Готов | 8 тестов |
| CombatSystem | ✅ Готов | 10 тестов (урон, уничтожение, friendly fire, reflective не уничтожается) |
| KnifeSystem | ✅ Готов | 30 тестов (спавн 3 типа, delayed, selection) |
| KnifeBounceSystem | ✅ Готов | в составе knife-тестов (отражение после Collision+Combat) |
| EnemySystem | ✅ Готов | 16 тестов (преследование, смерть, in-place velocity) |
| RewindSystem | ✅ Готов | 14 тестов (undo тика, drain TimeMana, stop-условия) |
| Renderer | ✅ Готов | без автотестов (визуальная проверка) |
| TimeSystem | ❌ | — |
| WaveSpawner | ❌ | — |
| ProgressionSystem | ❌ | — |
| SpellCardSystem | ❌ | — |

---

## Класс Game

| Элемент | Статус | Примечание |
|---------|--------|------------|
| `Game.__init__` | ✅ Готов | World + 10 систем + GameLoop + Renderer + EventLog + SnapshotBuffer |
| `_tick(dt)` | ✅ Готов | Rewind-gate: input → если rewind то undo+drain; иначе begin_tick→capture_fields→системы→snapshot_buffer.capture |
| `_rewind()` | ✅ Готов | InputSystem всегда; R+TimeMana → RewindSystem.start/update; иначе stop |
| `_render(alpha)` | ✅ Готов | Делегирует в Renderer.render(world, alpha) |
| `_check_quit` | ✅ Готов | ESC/Q → loop.stop (вызывается и в rewind-ветке) |
| `run()` / `stop()` | ✅ Готов | Делегирует в GameLoop |
| Порядок систем | ✅ | Input → PlayerMovement → Knife → Enemy → Movement → Separation → Collision → Combat → KnifeBounce → Lifetime |
| `main.py` | ✅ Готов | pygame.init → Game → ArenaSetup.setup → run → quit |

---

## Фаза 2 — Движение + Время

| Компонент | Статус |
|-----------|--------|
| Event Log (с Undo) | ✅ Готов (EventLog, 28 тестов) |
| Ring Buffer Snapshots | ✅ Готов (SnapshotBuffer, 24 теста) |
| Rewind (reverse replay) | ✅ Готов (RewindSystem, 14 тестов) |
| World hooks (record_*) | ✅ Готов (create/destroy/add/remove + `_undoing` флаг) |
| TimeSystem (local_time_scale, Time Stop, Slow) | ❌ |
| Selective Rewind + TimelineLayer | ❌ (вне MVP) |
| Time Bubble | ❌ (вне MVP) |

## Фаза 3 — Геймплей

| Компонент | Статус |
|-----------|--------|
| Knife System (3 типа MVP + 4 доп.) | ✅ 3 типа MVP: Normal, Delayed, Reflective |
| Knife Bounce (отдельная система) | ✅ Готов (после Collision+Combat) |
| Spell Cards (event-driven, мана) | ❌ 2 карты: knives-around + teleport-to-cursor |
| Способности времени (мана времени) | ❌ (TimeSystem) |
| Enemy System | ✅ Готов (преследование + смерть) |
| SeparationSystem (анти-стак) | ✅ Готов (отталкивание врагов) |
| Collision System | ✅ Готов | broad+narrow + CollisionFilter (битовые слои) + CollisionEvent |
| Player (Сакуя: HP + Mana + TimeMana + Experience) | ✅ Готов (спавн в ArenaSetup) |
| Player Movement (WASD) | ✅ Готов |
| Ввод / Управление | ✅ Готов | InputSystem: mouse + keyboard → InputState компонент |
| Рендеринг | ✅ Готов | Renderer: круги (player/enemy/knife) + HP-бар врагов |
| Спавн арены | ✅ Готов | `src/world_setup.py` ArenaSetup.setup |
| Точка входа | ✅ Готов | `main.py` |
| WaveSpawner (бесконечный спавн) | ❌ настраиваемый в config |
| Roguelike прогрессия (опыт, уровни, драфт) | ❌ XP-капли + draft 1-of-3 |
| UI (HUD: HP/Mana/TimeMana, спрайты) | ❌ |
| Спрайты объектов | ❌ |
| Музыка / звук | ❌ |
| Босс (1 шт.) | ❌ финал MVP |

## Фаза 4 — Продвинутые механики

| Компонент | Статус |
|-----------|--------|
| Rollback DSU | ❌ |
| Persistent Snapshots | ❌ |
| Sweep & Prune | ❌ |
| Timeline Fracture | ❌ (вне MVP) |
| Centralised config | ✅ Готов (`config/config_params.py`) |

---

## Проблемы, требующие внимания

1. **Нет тестов** — ✅ исправлено (262 теста)
2. **`game_loop.py` пустой** — ✅ исправлено
3. **`spatial_hash.py` пустой** — ✅ исправлено
4. **Docstring-несогласованность** — ✅ исправлено
5. **`__init__.py` в utils** — ✅ исправлено (SpatialHashGrid экспортирован)
6. **`CollisionSystem._handle_collision`** — ✅ исправлено (генерирует CollisionEvent)
7. **`World._is_alive` приватный** — тесты используют приватный API
8. **`Game._render` — заглушка** — ✅ исправлено (Renderer)
9. **Нет спавна игрока/врагов** — ✅ исправлено (ArenaSetup)
10. **`mouse._get_mouse_pos()`** — ✅ исправлено (`mouse.get_pos()`)
11. **KnifeSystem не спавнил ножи** (query KnifeLoadout+InputState на одной сущности) — ✅ исправлено (InputState ищется отдельно)
12. **GameLoop не обрабатывал pygame events** — ✅ исправлено (`pygame.event.pump()`)
13. **Скорости в px/сек применялись per-tick (120× быстрее)** — ✅ исправлено (делим на 120)
14. **Игрок не двигался (нет системы чтения WASD)** — ✅ исправлено (PlayerMovementSystem)
15. **Reflective ножи не отбивались** (bounce читал пустые events) — ✅ исправлено (KnifeBounceSystem после Combat)
16. **Враги стакались в точке (O(n²) в кластере)** — ✅ исправлено (SeparationSystem)
17. **`undo_latest_tick` не отменял ничего** (пустая реализация) — ✅ исправлено (reverse-undo 5 типов событий)
18. **`WorldSnapshot.capture` не копировал компоненты** — ✅ исправлено (copy.copy)
19. **`WorldSnapshot.restore` — `@staticmethod` + неверные типы** — ✅ исправлено
20. **RewindSystem drain мутировал висячую ссылку** (после undo объект заменён) — ✅ исправлено (get_component после undo)
21. **Game: нет EventLog/SnapshotBuffer + дубликат InputSystem** — ✅ исправлено
22. **Магические числа разбросаны по файлам** — ✅ исправлено (`config/config_params.py`)

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
20. ~~Реализовать KnifeSystem~~ ✅ (30 тестов, 3 типа ножей)
21. ~~Реализовать Game~~ ✅ (10 тестов)
22. ~~Реализовать EnemySystem~~ ✅ (16 тестов, преследование + смерть)
23. ~~Реализовать базовый рендеринг~~ ✅ (Renderer: круги + HP-бар)
24. ~~Реализовать спавн игрока и врагов~~ ✅ (ArenaSetup.setup)
25. ~~Реализовать PlayerMovementSystem (WASD)~~ ✅ (13 тестов)
26. ~~Реализовать KnifeBounceSystem~~ ✅ (отражение после Collision+Combat)
27. ~~Точка входа `main.py`~~ ✅
28. **MVP playable-прототип готов** ✅ (запускается, геймплей работает)
29. ~~Реализовать Event Log с Undo~~ ✅ (EventLog, 28 тестов)
30. ~~Реализовать Ring Buffer Snapshots~~ ✅ (SnapshotBuffer, 24 теста)
31. ~~Реализовать Rewind (reverse replay)~~ ✅ (RewindSystem, 14 тестов)
32. ~~World hooks для record_*~~ ✅ (create/destroy/add/remove + `_undoing`)
33. ~~Centralised config~~ ✅ (`config/config_params.py`)
34. ~~SeparationSystem (анти-стак врагов)~~ ✅ (13 тестов)
35. Реализовать **TimeSystem** (Time Stop / Slow, drain TimeMana, клавиши) — Фаза 2
36. Реализовать **WaveSpawner** (бесконечный спавн волн, параметры в config)
37. Реализовать **2 Spell Cards** (мана): knives-around-self + teleport-to-cursor
38. Реализовать **ProgressionSystem**: враги дропают XP+мана, level-up → draft 1-of-3 апгрейдов
39. Реализовать **UI + спрайты**: HUD (HP/Mana/TimeMana/уровень), спрайты вместо кругов
40. Добавить **музыку / звук** (pygame.mixer)
41. Реализовать **1 босса** (фаза боя, спец-атаки) — финал MVP
42. **MVP для показа готов** 🎯
