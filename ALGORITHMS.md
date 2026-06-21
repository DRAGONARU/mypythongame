# ALGORITHMS.md — Luna Dial Survivors

## О проекте

**Luna Dial Survivors** — bullet-heaven / roguelike-игра на Python 3.13 + Pygame,
посвящённая Сакуе Изайой из серии Touhou Project. Игрок выживает на арене против
бесконечных волн врагов, управляя временем (замедление, остановка, перемотка
назад) и используя спелл-карты.

### Технологии и архитектура

- **Язык:** Python 3.13
- **Графика/ввод:** Pygame
- **Архитектура:** Custom ECS (Entity-Component-System) на основе Sparse Set
- **Симуляция:** Fixed Tick Simulation (120 Гц) — детерминированный шаг логики,
  независимый от частоты кадров
- **Время:** перемотка реализована через reverse-replay (отмена событий в обратном
  порядке), а не через forward-replay
- **Тесты:** 447 автотестов (pytest)

### Структура кода

```
config/config_params.py     — все настраиваемые константы
src/core/ecs/               — Entity, SparseSet, World, Query, System
src/core/event_log.py       — журнал событий для перемотки (Undo)
src/core/snapshots.py       — ring buffer снапшотов мира
src/core/game_loop.py       — фиксированный игровой цикл
src/core/game.py            — оркестрация систем, перемотка, победа/поражение
src/core/components.py      — 20+ компонентов данных
src/core/events.py          — CollisionEvent
src/utils/spatial_hash.py   — SpatialHashGrid
src/systems/                — 15 систем (движение, бой, спавн, босс и др.)
src/rendering/              — Renderer, SpriteSheet
src/world_setup.py          — фабрика спавна игрока
main.py                     — точка входа
```

### Пайплайн систем (15 систем, порядок выполнения)

```
Input → PlayerMovement → Knife → SpellCard → Progression → Enemy → Boss
→ Movement → Separation → Collision → Combat → KnifeBounce → Lifetime
→ PlayerGain → WaveSpawner
```

---

## Реализованные алгоритмы

### 1. Sparse Set (разреженное множество)

**Файлы:** `src/core/ecs/sparse_set.py`, `src/core/ecs/world.py`

**Назначение:** хранилище компонентов в ECS. Каждый тип компонента хранится в
собственном SparseSet — структура данных, позволяющая итерировать только «живые»
значения без пропусков и проверок на `None`.

**Механизм работы:**

Внутри три параллельных массива:

| Массив         | Индекс        | Значение                          |
|----------------|---------------|-----------------------------------|
| `_sparse[eid]` | id сущности   | индекс в dense (-1 если нет)      |
| `_dense[i]`    | порядковый    | id сущности                       |
| `_values[i]`   | порядковый    | сам компонент                     |
| `_generations` | id сущности   | поколение (для защиты от dangling)|

- **Insert:** `_sparse[eid]` указывает на конец `_dense`; append в оба массива.
  O(1) амортизированно.
- **Get:** прямой доступ `_sparse[eid]` → `_values[idx]`. O(1).
- **Remove (swap-with-last):** заменяет удаляемый элемент последним из dense,
  обновляет sparse-индекс перемещённого элемента, затем `pop()`. Dense остаётся
  компактным — нет дырок. O(1).

**Сложность:**
- Insert / Get / Remove: **O(1)**
- Итерация по всем значениям: **O(N)**, где N — число живых компонентов

**Почему не dict:** итерация по SparseSet проходит по плотному массиву без дырок
и None-проверок, что критично при тысячах ножей и снарядов.

---

### 2. Generation Handles (поколения сущностей)

**Файлы:** `src/core/ecs/entity.py`, `src/core/ecs/world.py`

**Назначение:** предотвращение dangling references — обращений к уничтоженным
сущностям, чьи id могли быть переиспользованы.

**Механизм работы:**

`Entity` — frozen dataclass из двух полей: `(id, generation)`.

- При `destroy_entity`: `_generations[eid] += 1`, id попадает в `_free_ids`.
- При `create_entity`: переиспользуется id из `_free_ids` (LIFO), но текущее
  значение `_generations[eid]` встраивается в новый Entity-хендл.
- Любая операция (get, remove, destroy) сверяет `entity.generation` с
  `_generations[eid]`. Несовпадение → отказ.

**Сложность:** проверка поколения — **O(1)** на каждую операцию с компонентом.

---

### 3. Query (мультикомпонентный запрос с выбором driving set)

**Файл:** `src/core/ecs/query.py`

**Назначение:** итерация по всем сущностям, обладающим набором компонентов
(например, `query(Player, Health, Position)`).

**Механизм работы:**

1. Среди запрошенных типов выбирается SparseSet с **наименьшим** числом элементов
   (driving set) — это минимизирует количество итераций внешнего цикла.
2. Для каждой сущности из driving set проверяется наличие остальных компонентов
   через O(1) `SparseSet.get`.
3. Если все найдены — собирается кортеж значений в порядке запрошенных типов и
   yield-ится.

**Сложность:**
- Выбор driving set: **O(K)**, K — число типов в запросе
- Итерация: **O(M × K)**, где M — размер driving set, K — число доп. проверок
  (каждая O(1))

---

### 4. Fixed Tick Simulation (фиксированный шаг симуляции)

**Файл:** `src/core/game_loop.py`

**Назначение:** детерминированная симуляция с постоянной частотой логики
независимо от FPS рендера. Необходима для корректной перемотки (reverse-replay
отменяет целые тики, а не дробные состояния).

**Механизм работы (accumulator pattern):**

1. Измеряется реальное время между кадрами: `real_dt = perf_counter() - prev`.
2. `real_dt` добавляется в аккумулятор (capped на 0.25 с против спайков).
3. Пока `accumulator >= FIXED_DT` (1/120 с): вызывается `tick_fn(FIXED_DT)`,
   аккумулятор уменьшается.
4. **Spiral of death guard:** если за один кадр выполнено `MAX_TICKS_PER_FRAME`
   (5) тиков, а аккумулятор всё ещё > FIXED_DT — он сбрасывается в 0 (жертвуем
   точностью ради выхода из спирали).
5. Остаток аккумулятора / FIXED_DT = `alpha` ∈ [0, 1) — фактор интерполяции для
   рендера.

**Сложность:** O(1) на кадр + O(T × S), где T — число тиков за кадр (≤5),
S — суммарная сложность всех систем.

**Следствие:** вся игровая логика работает в «тиках» (1 тик = 1/120 с), а не в
секундах. Скорости задаются как `value / TICK_RATE` и применяются per-tick.

---

### 5. Spatial Hash Grid (пространственный хеш)

**Файл:** `src/utils/spatial_hash.py`

**Назначение:** broad-phase фильтрация кандидатов для коллизий и separation.
Снижает сложность проверки столкновений с O(N²) до ~O(N) для равномерно
распределённых объектов.

**Механизм работы:**

- Пространство делится на квадратные ячейки размера `cell_size`.
- Каждая сущность помещается в **одну** ячейку по центру позиции:
  `cell = (int(x // cell_size), int(y // cell_size))`.
- Хранение: `_cells: dict[(cx,cy), set[Entity]]` + обратный индекс
  `_entity_cells: dict[Entity, (cx,cy)]`.
- `query_circle(x, y, radius)`: вычисляет диапазон ячеек, перекрывающих круг
  `(±cell_radius)`, и собирает все сущности из них. Возвращает кандидатов —
  узкая фаза (narrow-phase, проверка расстояния) остаётся за вызывающим.

**Сложность:**
- Insert / Remove: **O(1)**
- Query: **O(C)**, C — число ячеек в окне запроса × сущностей в них
  (для cell_size ≥ max_radius — константа ~9 ячеек)
- Полный проход коллизий: **O(N × C_avg)** вместо O(N²)

**Особенность:** пустые ячейки удаляются из dict для предотвращения утечек памяти
при частых spawn/despawn.

---

### 6. Collision Filter (битовые маски слоёв)

**Файлы:** `src/core/components.py` (`CollisionFilter`, `LAYER_*`),
`src/systems/collision_system.py`

**Назначение:** фильтрация пар столкновений по слоям (ножи не сталкиваются с
ножами, снаряды босса — только с игроком и т.д.) без лишних narrow-phase проверок.

**Механизм работы:**

- Каждому слою присвоена степень двойки:
  `LAYER_PLAYER=1, LAYER_ENEMY=2, LAYER_KNIFE=4, LAYER_PROJECTILE=8, …`
- Компонент `CollisionFilter` хранит `layer` (свой слой) и `mask` (с кем
  сталкиваться).
- Проверка: две сущности A и B сталкиваются, если
  `(A.layer & B.mask) and (B.layer & A.mask)` — обе должны «хотеть» столкновения
  друг с другом.
- Проверка выполняется **до** narrow-phase (расстояние), отсекая несовместимые
  пары за O(1).

**Сложность:** **O(1)** на пару сущностей (битовые операции).

---

### 7. Narrow-phase Collision Detection (окружности)

**Файл:** `src/systems/collision_system.py`

**Назначение:** точная проверка столкновения двух круглых коллайдеров после
broad-phase фильтрации.

**Механизм работы:**

Для каждой сущности берутся кандидаты из SpatialHashGrid. Для каждой пары
(с `id` дубликат-фильтром `other.id < entity.id → skip`, чтобы обработать пару
один раз):

1. Проверка CollisionFilter (см. алгоритм 6).
2. Расчёт `dist_sq = dx² + dy²` (без sqrt для сравнения).
3. Если `dist_sq ≤ (r1 + r2)²` → столкновение, создаётся `CollisionEvent`.

**Сложность:** O(1) на пару; суммарно O(N × C_avg) после broad-phase.

---

### 8. Separation System (анти-стак врагов)

**Файл:** `src/systems/separation_system.py`

**Назначение:** предотвращение наложения врагов друг на друга. Без этого все
враги, преследующие игрока, сходятся в одну точку → O(N²) в одной ячейке grid.

**Механизм работы:**

1. Собственный SpatialHashGrid только по врагам.
2. Для каждой пары пересекающихся врагов (через `query_circle`):
   - Вычисляется нормаль `(nx, ny)` по вектору между центрами.
   - `overlap = (r1 + r2) - dist`.
   - **Оба** врага смещаются на `overlap / 2` вдоль нормали в противоположные
     стороны (мгновенная коррекция позиции, не через velocity).
3. Фильтр `other.id <= entity.id → skip` — каждая пара обрабатывается один раз.

**Сложность:** O(N × C_avg), где C_avg — кандидаты в окрестности.

**Особенность:** позиционная коррекция, не генерирует CollisionEvents (чтобы
CombatSystem не тратил циклы на пары враг-враг).

---

### 9. Event Log + Reverse-Replay Rewind (перемотка назад)

**Файлы:** `src/core/event_log.py`, `src/systems/rewind_system.py`

**Назначение:** перемотка игрового времени назад на N тиков. Реализована через
отмену событий в обратном порядке (reverse-replay), а не через пересчёт с начала
(forward-replay).

**Механизм работы:**

**EventLog** — ring buffer из «бакетов» по тикам. Каждый бакет — список
`UndoEvent`:

| kind        | Когда записывается         | Undo действие                         |
|-------------|----------------------------|---------------------------------------|
| `field`     | capture_fields (до систем) | перезаписать компонент копией до мута |
| `added`     | add_component (новый)      | remove_component                      |
| `removed`   | remove_component           | re-add копию                          |
| `created`   | create_entity              | destroy_entity                        |
| `destroyed` | destroy_entity             | вручную восстановить gen + компоненты |

- **capture_fields:** перед выполнением систем делает `copy.copy()` каждого
  компонента (кроме Mana/TimeMana — их drain должен персистить) и сохраняет как
  `field`-события. Дальнейшие in-place мутации систем можно отменить.
- **undo_latest_tick:** итерирует бакет последнего тика **в обратном порядке**,
  применяет обратное действие для каждого события, декрементирует `world.tick`.
- Флаг `_undoing` в World предотвращает рекурсивную запись undo-событий при
  откате.
- **`_undo_destroyed`** вручную восстанавливает `_generations[eid]`, убирает id
  из `_free_ids`, инкрементирует `_alive` — нельзя использовать `create_entity`,
  т.к. он выдаст новое поколение.

**RewindSystem** оборачивает EventLog:
- `start()` — игрок зажал R + есть TimeMana.
- `update()` — за каждый вызов отменяет один тик, тратит `REWIND_DRAIN_PER_TICK`
  TimeMana (после undo, чтобы избежать висячей ссылки).
- Стоп-условия: нет маны / достигнут `MAX_REWIND_TICKS` / пустой лог /
  неудачный undo / нет игрока.

**Сложность:**
- capture_fields (per tick): **O(N_total)**, N_total — суммарно компонентов
- undo_latest_tick: **O(E)**, E — число событий в тике (обратная итерация)
- Хранение: **O(capacity × E_avg)** памяти

**Исключение Mana/TimeMana из capture:** иначе undo восстанавливал бы
пред-тиковое значение маны каждый раз, и drain перемотки бы «отменялся» — мана
бы осциллировала и не тратилась.

---

### 10. Snapshot Ring Buffer (кольцевой буфер снапшотов)

**Файлы:** `src/core/snapshots.py`

**Назначение:** хранение полных копий состояния мира на каждый тик. Альтернатива
EventLog для сценария «мгновенный откат к точке во времени». В MVP используется
как резервный механизм рядом с EventLog.

**Механизм работы:**

**WorldSnapshot.capture:**
- Для каждого типа компонента: `[(Entity, copy.copy(comp))]` — список пар.
- Копии `_generations`, `_free_ids`, `_next_id`, `_alive`.

**WorldSnapshot.restore:**
- Пересоздаёт SparseSet для каждого типа, вставляет копии компонентов.
- Восстанавливает все книги сущностей.

**SnapshotBuffer** — кольцевой буфер:
- `_buffer: list[WorldSnapshot | None]` размера `capacity`.
- `_head` — указатель записи, движется по модулю capacity.
- `capture`: пишет в `_buffer[_head]`, `_head = (_head + 1) % capacity`.
- `restore(tick)`: вычисляет индекс через смещение от oldest, восстанавливает,
  **обрезает** `_count` (отбрасывает «будущее» для alternate timeline).
- `oldest_tick` / `latest_tick` — границы доступного окна.

**Сложность:**
- Capture: **O(N_total)** — shallow copy всех компонентов
- Restore: **O(N_total)** — пересоздание SparseSet
- Память: **O(capacity × N_total)** — тяжёлый по памяти, поэтому capacity=240

**Отличие от EventLog:** snapshot — полное состояние, EventLog — дельты. Snapshot
надёжнее (не зависит от корректности записи событий), но дороже по памяти.

---

### 11. Time System (локальный масштаб времени)

**Файлы:** `src/systems/time_system.py`, `src/core/components.py` (`TimeAffected`)

**Назначение:** замедление (Slow) и полная остановка (Time Stop) времени для
всех сущностей, кроме игрока.

**Механизм работы:**

- `TimeAffected.scale` — множитель скорости на сущности (1.0 = нормально).
- `MovementSystem` применяет `position += velocity × TimeAffected.scale` — таким
  образом scale=0 «замораживает» сущность, scale=0.3 замедляет в ~3.3×.
- TimeSystem один раз за тик устанавливает scale для всех сущностей:
  - Игрок: всегда `1.0` (двигается нормально).
  - Delayed-ножи: всегда `0.0` (управляются KnifeSystem, не глобальным временем).
  - Остальные: `1.0` (Normal), `SLOW_SCALE` (Slow), `0.0` (Time Stop).
- `current_scale` property выставляет глобальный масштаб — используется
  PlayerGainSystem (реген реже при Slow, отключён при Time Stop) и BossSystem
  (не стреляет при Time Stop).

**Сложность:** **O(N)** за тик (один проход по всем TimeAffected).

---

### 12. Damage Cooldown (кулдаун получения урона)

**Файлы:** `src/systems/combat_system.py`, `src/core/components.py` (`DamageCooldown`)

**Назначение:** предотвращение получения 120 попаданий/сек при постоянном
контакте (враг касается игрока, снаряд босса висит в игроке).

**Механизм работы:**

- При получении урона игроку добавляется `DamageCooldown(remaining_ticks=30)`.
- CombatSystem каждый тик декрементирует `remaining_ticks`; при ≤0 удаляет
  компонент.
- Пока `DamageCooldown` присутствует — контактный урон не наносится (early return).
- 30 тиков = 0.25 с при 120 Гц.

**Сложность:** O(D) за тик, D — число сущностей с активным кулдауном.

---

### 13. Wave Spawner (пульсный спавн волн)

**Файл:** `src/systems/wave_spawner_system.py`

**Назначение:** бесконечный спавн врагов по краям экрана с фиксированным
кулдауном и общим лимитом.

**Механизм работы:**

- Каждые `WAVE_SPAWN_COOLDOWN` тиков спавнится пульс из `WAVE_SPAWN_COUNT`
  врагов.
- Позиция — случайная точка на одной из 4 сторон экрана (`randint(0,3)` →
  координаты на этой стороне).
- `total_spawned` отслеживает бюджет; последняя пульсация добивает остаток
  `min(count, remaining)`.
- `all_spawned` property — `total_spawned >= max_enemies`.
- Первый пульс срабатывает сразу (`_cooldown_ticks=0` изначально).

**Сложность:** O(K) за пульс, K — число врагов в пульсе (создание сущностей +
компонентов).

---

### 14. Progression System (XP-орбы, подбор, левел-ап)

**Файл:** `src/systems/progression_system.py`

**Назначение:** roguelike-прогрессия — враги дропают сферы опыта, при накоплении
X опыта повышается случайная характеристика.

**Механизм работы:**

1. **Дроп:** для каждого врага с `Health <= 0` (до того как EnemySystem уничтожит
   труп) спавнится `XPOrb` на его позиции.
2. **Подбор:** игрок собирает орбы в радиусе `XP_PICKUP_RADIUS` — проверка
   `dist² ≤ r²` (без sqrt). Собранные орбы уничтожаются, value добавляется в
   `Experience.current`.
3. **Level-up:** пока `current >= to_next`: вычитает порог, инкрементирует level,
   умножает порог на `XP_GROWTH` (1.5), применяет один случайный апгрейд из
   `random.choice(pool)`.

Пулл апгрейдов: max HP, max Mana, max TimeMana, кол-во отскоков ножа, кол-во ножей
в кольце спелл-карты.

**Сложность:**
- Дроп: O(E), E — число мёртвых врагов
- Подбор: O(Orbs) — линейный проход по всем орбам с O(1) проверкой дистанции
- Level-up: O(L), L — число уровней за тик (обычно 1)

---

### 15. Boss Spread Fire (веерная стрельба босса)

**Файл:** `src/systems/boss_system.py`

**Назначение:** босс стреляет 3 снарядами — центральный в игрока, боковые под
±20°.

**Механизм работы:**

1. `base_angle = atan2(player.y - boss.y, player.x - boss.x)` — угол на игрока.
2. Для каждого `delta` из `(-20°, 0°, +20°)`:
   - `angle = base_angle + delta`
   - `vx = cos(angle) × speed`, `vy = sin(angle) × speed`
   - Спавн `Projectile` с Position, Velocity, Collider, Lifetime, CollisionFilter.
3. Каждый босс имеет **независимый** `fire_cooldown` (в компоненте `Boss`), чтобы
   несколько боссов стреляли асинхронно.
4. Стрельба подавляется при Time Stop (`current_scale <= 0`).

**Сложность:** O(B × 3) за тик, B — число боссов; O(1) на снаряд.

---

### 16. Knife Bounce (отражение от врагов)

**Файл:** `src/systems/knife_system.py` (`KnifeBounceSystem`)

**Назначение:** reflective-ножи отскакивают от врагов, используя формулу
отражения вектора от нормали.

**Механизм работы:**

Для каждого `CollisionEvent` (после Combat, чтобы нож пережил попадание):
1. Проверка, что одна из сущностей — Reflective-нож, другая — Enemy.
2. Нормаль `n = (boss_pos - knife_pos) / dist` — от врага к ножу.
3. Отражение: `v' = v - 2(v·n)n` (классическая формула отражения).
4. Коррекция позиции: выталкивание ножа из пересечения вдоль нормали.
5. `bounces_remaining -= 1`; при 0 компонент `Reflective` удаляется (нож
   становится обычным и уничтожится при следующем попадании).

**Сложность:** O(E) за тик, E — число CollisionEvents.

---

### 17. Sprite Rotation Caching (поворот спрайтов ножей)

**Файл:** `src/rendering/render.py`

**Назначение:** визуальное вращение спрайта ножа по направлению полёта.

**Механизм работы:**

- `angle = -degrees(atan2(vel.y, vel.x))` — угол в градусах (инверсия Y из-за
  экранных координат).
- `pygame.transform.rotate(sprite, angle)` — создаёт новый Surface.
- Центровка: `rotated.get_rect(center=(x, y))`.

**Сложность:** O(1) на нож, но `transform.rotate` аллоцирует новый Surface каждый
вызов — потенциальное узкое место при тысячах ножей. Кеширование по углу —
возможная оптимизация.

---

### 18. Ring Buffer eviction (вытеснение в кольцевых буферах)

**Файлы:** `src/core/event_log.py`, `src/core/snapshots.py`

**Назначение:** ограничение потребления памяти при хранении истории за N тиков.

**Механизм работы:**

**EventLog:**
- `_tick_order: list[int]` — порядок тиков, `_events: dict[int, list]`.
- При `begin_tick`: append тика в `_tick_order`. Если `len > capacity` —
  `pop(0)` из `_tick_order` и `pop` из `_events`. O(1) амортизированно
  (pop(0) — O(K), но K = capacity, константа).

**SnapshotBuffer:**
- `_buffer` — pre-allocated list размера `capacity`.
- `_head = (_head + 1) % capacity` — перезапись старейшего слота.
- `_count = min(count + 1, capacity)` — отслеживание заполненности.
- `oldest_tick`: если буфер заполнен — `_buffer[_head]` (слот, который будет
  перезаписан следующим); иначе `_buffer[0]`.

**Сложность:** O(1) на capture/evict.

---

## Сводная таблица сложности

| Алгоритм                        | Per-tick сложность      | Память                  |
|---------------------------------|-------------------------|-------------------------|
| Sparse Set operations           | O(1) insert/get/remove  | O(N) на тип компонента  |
| Query (multi-component)         | O(M × K)                | O(1)                    |
| Spatial Hash Grid (broad-phase) | O(N × C_avg)            | O(N)                    |
| Collision narrow-phase          | O(N × C_avg)            | O(1)                    |
| Separation                      | O(N × C_avg)            | O(N)                    |
| Event Log capture_fields        | O(N_total)              | O(capacity × E_avg)     |
| Event Log undo_latest_tick      | O(E_tick)               | —                       |
| Snapshot capture/restore        | O(N_total)              | O(capacity × N_total)   |
| Wave Spawner (per pulse)        | O(K)                    | O(1)                    |
| Progression (pickup)            | O(Orbs)                 | O(Orbs)                 |
| Boss fire                       | O(B × 3)                | O(1)                    |
| Knife bounce                    | O(E_events)             | O(1)                    |
| Time System                     | O(N_time_affected)      | O(1)                    |

Где:
- N — число сущностей соответствующего типа
- C_avg — среднее число кандидатов из broad-phase (константа при cell_size ≥ max_radius)
- E — число событий
- K — число типов в запросе / врагов в пульсе
