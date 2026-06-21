# PROGRESS — Прогресс проекта

## Последняя проверка: 2026-06-22

---

## Инфраструктура

| Элемент | Статус | Примечание |
|---------|--------|------------|
| `pyproject.toml` | ✅ Готов | Имя, зависимости, pytest-конфиг, build-system |
| Структура папок `src/` | ✅ Создана | core, entities, systems, rendering, input, audio, ui, utils, world |
| `__init__.py` во всех пакетах | ✅ Готов | Все 9 пакетов + core/ecs |
| `tests/` | ✅ 447 тестов | entity(8), sparse_set(22), world(35), query(20), system(10), game_loop(11), spatial_hash(29), movement(7), player_movement(13), input(5), collision(11), lifetime(8), combat(25), game(13), knife(30), enemy(16), separation(13), snapshots(24), event_log(28), rewind(18), time_system(24), wave_spawner(9), spell_card(14), progression(18), boss(21) — все проходят |
| `assets/` | ⚠️ Пустая | Нет ассетов |
| `config/` | ✅ Готов | `config_params.py` — все константы (tick, rewind, player, enemy, knife, spatial, rendering, HUD, sprites, bg, audio, spell, progression, boss) |
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
| KnifeLoadout | ✅ | current, available, cooldown, reflective_bounces |
| SpellLoadout | ✅ | current, available, cooldown, knives_count |
| Boss | ✅ | fire_cooldown |
| Sprite | ❌ | texture_id, layer |
| Animation | ❌ | current_frame, frame_timer |
| TimelineAnchor | ❌ | timeline_id |
| Frozen | ❌ | remaining_ticks |
| SpellCard | ❌ | spell_type, remaining_ticks, cooldown |
| TimeBubble | ❌ | center_x, center_y, radius, scale, falloff |
| Projectile | ✅ | damage |
| XPOrb | ✅ | value |
| DamageCooldown | ✅ | remaining_ticks |

---

## Системы

| Система | Статус | Тесты |
|---------|--------|-------|
| MovementSystem | ✅ Готов | 7 тестов (velocity × TimeAffected.scale per-tick) |
| PlayerMovementSystem | ✅ Готов | 13 тестов (WASD, диагональ-нормализация, in-place) |
| InputSystem | ✅ Готов | 5 тестов (пишет InputState в World) |
| TimeSystem | ✅ Готов | 24 теста (Normal/Slow/TimeStop, drain, priority, delayed-safe) |
| CollisionSystem | ✅ Готов | 11 тестов (broad+narrow + CollisionFilter + CollisionEvent) |
| SeparationSystem | ✅ Готов | 13 тестов (анти-стак врагов, свой grid) |
| LifetimeSystem | ✅ Готов | 8 тестов |
| CombatSystem | ✅ Готов | 22 теста (ножи + контактный урон враг→игрок + DamageCooldown) |
| KnifeSystem | ✅ Готов | 30 тестов (спавн 3 типа, delayed, selection) |
| KnifeBounceSystem | ✅ Готов | в составе knife-тестов (отражение после Collision+Combat) |
| EnemySystem | ✅ Готов | 16 тестов (преследование, смерть, in-place velocity) |
| RewindSystem | ✅ Готов | 18 тестов (undo тика, drain TimeMana, stop-условия, return bool) |
| Renderer | ✅ Готов | спрайты (sheet/rect), HUD-полоски, HP-бары, тайловый фон, XP-орбы, XP-бар (низ), wave-бар (верх) (без автотестов) |
| SpriteSheet | ✅ Готов | листы с разными размерами ячеек + get_rect |
| PlayerGainSystem | ✅ Готов | пассивный реген HP/Mana/TimeMana, масштабируется TimeSystem (без автотестов) |
| WaveSpawner | ✅ Готов | 9 тестов (пульсный спавн по краям, кулдаун, лимит, all_spawned) |
| SpellCardSystem | ✅ Готов | 14 тестов (knives кольцо + teleport, правый клик, Z-смена, мана, кулдаун) |
| ProgressionSystem | ✅ Готов | 18 тестов (XP-орбы, подбор, level-up, 5 апгрейдов) |
| BossSystem | ✅ Готов | 21 тест (спавн последним, движение, веер ±20°, независимый кулдаун, смерть) |

---

## Класс Game

| Элемент | Статус | Примечание |
|---------|--------|------------|
| `Game.__init__` | ✅ Готов | World + 15 систем + GameLoop + Renderer + EventLog + SnapshotBuffer + TimeSystem + WaveSpawner + BossSystem + музыка |
| `_tick(dt)` | ✅ Готов | Rewind-gate: input → если rewind то undo+drain; иначе begin_tick→capture_fields→time_system→системы→snapshot_buffer.capture + _check_player_death + _check_victory |
| `_rewind()` | ✅ Готов | InputSystem всегда; R+TimeMana → RewindSystem.start/update (возвращает bool); иначе stop |
| `_render(alpha)` | ✅ Готов | Делегирует в Renderer.render(world, alpha, wave_progress) |
| `_wave_progress()` | ✅ Готов | killed = total_spawned - alive, ratio = killed / max_enemies |
| `_check_quit` | ✅ Готов | ESC/Q → loop.stop (вызывается и в rewind-ветке) |
| `_check_player_death` | ✅ Готов | HP ≤ 0 → loop.stop |
| `_check_victory` | ✅ Готов | all_spawned AND boss_spawned AND нет живых врагов → victory=True, loop.stop |
| `_start_music` | ✅ Готов | pygame.mixer зацикленный трек, try/except fallback |
| `run()` / `stop()` | ✅ Готов | Делегирует в GameLoop |
| Порядок систем | ✅ | Input → PlayerMovement → Knife → SpellCard → Progression → Enemy → Boss → Movement → Separation → Collision → Combat → KnifeBounce → Lifetime → PlayerGain → WaveSpawner |
| `main.py` | ✅ Готов | pygame.init → Game → ArenaSetup.setup(enemy_count=0) → run → quit |

---

## Фаза 2 — Движение + Время

| Компонент | Статус |
|-----------|--------|
| Event Log (с Undo) | ✅ Готов (EventLog, 28 тестов, TimeMana/Mana исключены из capture — drain персистит) |
| Ring Buffer Snapshots | ✅ Готов (SnapshotBuffer, 24 теста, обрезка future после restore) |
| Rewind (reverse replay) | ✅ Готов (RewindSystem, 18 тестов, update возвращает bool) |
| World hooks (record_*) | ✅ Готов (create/destroy/add/remove + `_undoing` флаг) |
| TimeSystem (local_time_scale, Time Stop, Slow) | ✅ Готов (24 теста; Space=Stop, E=Slow; delayed-safe) |
| Selective Rewind + TimelineLayer | ❌ (вне MVP) |
| Time Bubble | ❌ (вне MVP) |

## Фаза 3 — Геймплей

| Компонент | Статус |
|-----------|--------|
| Knife System (3 типа MVP + 4 доп.) | ✅ 3 типа MVP: Normal, Delayed, Reflective |
| Knife Bounce (отдельная система) | ✅ Готов (после Collision+Combat) |
| Spell Cards (event-driven, мана) | ✅ Готов (SpellCardSystem: knives-around + teleport, правый клик, Z-смена) |
| Способности времени (мана времени) | ✅ Готов (TimeSystem: Space=Stop, E=Slow) |
| Enemy System | ✅ Готов (преследование + смерть, босс пропускается) |
| Enemy contact damage | ✅ Готов (DamageCooldown, враг→игрок, смерть игрока) |
| SeparationSystem (анти-стак) | ✅ Готов (отталкивание врагов) |
| Collision System | ✅ Готов | broad+narrow + CollisionFilter (битовые слои) + CollisionEvent |
| Player (Сакуя: HP + Mana + TimeMana + Experience) | ✅ Готов (спавн в ArenaSetup) |
| Player Movement (WASD) | ✅ Готов |
| Ввод / Управление | ✅ Готов | InputSystem: mouse + keyboard → InputState компонент |
| Рендеринг | ✅ Готов | Renderer: спрайты (sheet+rect), HP-бары врагов, HUD-полоски, тайловый фон, XP-орбы, XP-бар (низ), wave-бар (верх) |
| Спрайты объектов | ✅ Готов | SpriteSheet (много листов, разные размеры ячеек, поворот ножей, спрайт босса) |
| UI (HUD: HP/Mana/TimeMana) | ✅ Готов | три полоски в верхнем левом углу + XP-бар внизу + wave-бар вверху |
| Музыка / звук | ✅ Готов | фоновый трек (pygame.mixer, зацикленный, fallback) + смена трека при спавне босса |
| Спавн арены | ✅ Готов | `src/world_setup.py` ArenaSetup.setup (только игрок, враги — WaveSpawner) |
| Точка входа | ✅ Готов | `main.py` |
| WaveSpawner (бесконечный спавн) | ✅ Готов (пульсный спавн по краям, кулдаун + лимит в config, all_spawned) |
| PlayerGainSystem (реген) | ✅ Готов (пассивный реген HP/Mana/TimeMana, масштаб TimeSystem) |
| Roguelike прогрессия (опыт, уровни) | ✅ Готов (XP-орбы, подбор по радиусу, level-up → случайный апгрейд из 5) |
| Босс | ✅ Готов (спавнится последним, движение к игроку, веер ±20°, независимый кулдаун, смена музыки) |

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
23. **Arrow keys / LShift oversized keycodes** (`get_pressed()` tuple=512, K_LSHIFT>512) — ✅ исправлено (`_is_pressed` bounds-check; Slow на K_e)
24. **TimeSystem `player_entity` не инициализирован** (UnboundLocalError когда игрока нет) — ✅ исправлено
25. **Rewind мана не тратилась** (TimeMana захватывался в field events, undo восстанавливал) — ✅ исправлено (TimeMana/Mana исключены из capture_fields)
26. **Стазис на последнем снапшоте** (`_rewind` возвращал True даже при неудачном undo) — ✅ исправлено (update возвращает bool)
27. **Враги не атаковали игрока** (CombatSystem обрабатывал только ножи) — ✅ исправлено (контактный урон + DamageCooldown)
28. **Delayed ножи летели как обычные** (TimeSystem перетирал scale=0 на 1.0) — ✅ исправлено (delayed-safe в `_apply_multiplier`)
29. **`No module named 'src'`** при запуске не из корня — ✅ исправлено (pyproject `where=["."]`, `src/__init__.py`, editable reinstall)
30. **Multiple bosses firing only one** (`_find_boss_pos` возвращал первого босса через `return` в цикле) — ✅ исправлено (итерация по всем боссам, независимый `fire_cooldown` в компоненте `Boss`)
31. **Spell card Z-cycle every tick** (edge-detection отсутствует, Z удерживается → циклит 120/сек) — ⚠️ консистентно с остальным кодом (single-press edge-detection — отдельная задача)

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
35. ~~Реализовать TimeSystem~~ ✅ (24 теста; Space=Stop, E=Slow, delayed-safe)
36. ~~Враги атакуют игрока~~ ✅ (контактный урон + DamageCooldown, 22 теста combat)
37. ~~Спрайты объектов~~ ✅ (SpriteSheet, много листов, разные размеры, поворот ножей)
38. ~~UI HUD~~ ✅ (полоски HP/Mana/TimeMana в верхнем левом углу)
39. ~~Тайловый фон~~ ✅ (кешированный `_bg`, fallback на fill)
40. ~~Музыка~~ ✅ (pygame.mixer зацикленный трек, fallback)
41. ~~Пакетная установка (No module named 'src')~~ ✅ (pyproject + editable reinstall)
42. ~~Реализовать **WaveSpawner**~~ ✅ (9 тестов, пульсный спавн по краям)
43. ~~Реализовать **PlayerGainSystem**~~ ✅ (реген, масштаб TimeSystem)
44. ~~Реализовать **2 Spell Cards**~~ ✅ (14 тестов, knives-around + teleport)
45. ~~Реализовать **ProgressionSystem**~~ ✅ (18 тестов, XP-орбы + level-up + 5 апгрейдов)
46. ~~Реализовать **босса**~~ ✅ (21 тест, спавн последним, движение, веер ±20°, смена музыки)
47. ~~**ALGORITHMS.md**~~ ✅ (18 алгоритмов с описанием и сложностью)
48. **MVP для показа готов** 🎯
