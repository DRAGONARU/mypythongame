# PLAN — Luna Dial Survivors

## Стек технологий
- **Python 3.13**
- **Pygame** — рендеринг, ввод, звук

## Архитектурные принципы
- **ООП** — объектно-ориентированный дизайн: классы, наследование, полиморфизм, инкапсуляция
- **SOLID** — каждый класс делает одну вещь (SRP), открыт для расширения но закрыт для изменения (OCP), подтипы заменяемы (LSP), узкие интерфейсы (ISP), зависимость от абстракций (DIP)
- **DRY** — нет дублирования логики; общее выносится в утилиты/базовые классы
- **KISS** — простые понятные решения; без избыточной абстракции там, где не нужно

## Качество кода
- Сложные алгоритмы и структуры данных (графы, очереди с приоритетом, пространственное индексирование и т.д.)
- Покрытие тестами (unit + integration)
- Понятные имена, без лишних комментариев-капитана

## Структура проекта (предварительно)
```
src/
  core/       — ядро: игровой цикл, конфигурация, константы
  entities/   — игровые сущности (персонажи, объекты)
  systems/    — системы/механики (физика, ИИ, путь, бой)
  rendering/  — отрисовка, камера, спрайты, анимации
  input/      — обработка ввода (клавиатура, мышь, геймпад)
  audio/      — звук и музыка
  ui/         — интерфейс (меню, HUD, диалоги)
  world/      — карта, уровень, тайлы, генерация
  utils/      — утилиты: матрица, векторы, структуры данных
tests/        — тесты (зеркальная структура src/)
assets/       — спрайты, звуки, шрифты, данные уровней
config/       — конфиги (JSON/YAML) для баланса, уровней и т.п.
```

## Концепция игры

**Bullet Heaven / Roguelike + Time Manipulation Sandbox + Dense ECS Simulation**

Персонаж — Сакуя (Touhou). Управление временем + ножи + spell cards.

### Ресурсы игрока
| Ресурс | Компонент | Назначение |
|--------|-----------|------------|
| Здоровье | Health | HP, при 0 — смерть |
| Мана | Mana | Spell cards: особые паттерны ножей, баффы характеристик, не-временная магия |
| Мана времени | TimeMana | Способности управления временем: Time Stop, Slow, Fast, Rewind, Time Bubbles |

Мана и мана времени — **независимые** ресурсы с отдельными запасами и регенерацией.

### Ножи (Knife System)
| Тип | Поведение | Приоритет |
|-----|-----------|-----------|
| Normal | стандартный проджектайл | **MVP** |
| Delayed | стоит на месте (timescale=0), потом активируется (timescale=1) | **MVP** |
| Reflective | рикошет от поверхностей | **MVP** |
| TimeAnchored | игнорирует global time stop | Средний |
| Orbiting | вращение вокруг цели | Средний |
| Piercing | проходит через врагов | Средний |
| Recursive | при rewind не откатывается, сохраняет trajectory memory | Средний |

Атаки: бросок ножа в сторону курсора (projectile), способности применяются по курсору или вокруг игрока (в зависимости от способности).

### Манипуляции со временем
| Эффект | scale | Область |
|--------|-------|---------|
| normal | 1.0 | глобально |
| slow | 0.2 | глобально / радиус |
| fast | 3.0 | глобально / радиус |
| stopped | 0.0 | глобально / радиус |
| reverse | -1.0 | rewind |

**Time Bubble** — расходует ману времени. Spell card создаёт: center, radius, timescale, falloff.
Каждый объект имеет `local_time_scale`. Обновление: `position += velocity * dt * local_time_scale`.

### Spell Cards
Расходуют **ману**. Event-driven: OnTick, OnHit, OnFreeze, OnRewind, OnTimeStop.
Типы: особые паттерны ножей, временные баффы характеристик, не-временная магия.

### Способности времени
Расходуют **ману времени**. Скорость расхода зависит от способности:
| Способность | Расход маны времени |
|-------------|---------------------|
| Time Stop | быстрый (держать = тратить) |
| Slow / Fast | средний (зонный, пока активен) |
| Rewind | быстрый (за каждый откатываемый тик) |
| Time Bubble | медленный (однократный при касте + медленный дрен пока активен) |

### Timeline Fracture (ветвление timelines) - **ВНЕ MVP**
Rewind не удаляет старую timeline. Каждая entity имеет `timeline_id`.
Можно: сражаться с прошлой версией себя, видеть старые ножи, накладывать timelines.
*Примечание: Полноценное ветвление отложено до будущих версий, в MVP реализуется только классический откат.*

### Прогрессия (Roguelike)
С врагов падает:
- **Мана / Мана времени** — восполнение ресурсов при убийстве
- **Опыт** — накапливается, при наборе достаточного количества → повышение уровня

Повышение уровня даёт:
1. **Небольшое повышение базовых статов** (здоровье, мана, мана времени, скорость и т.д.)
2. **Случайный выбор из 3 вариантов** (рогалик-драфт):
   - Улучшить конкретный тип ножей в арсенале (урон, скорость, количество и т.п.)
   - Добавить новый тип ножей
   - Добавить / заменить spell card
   - Улучшить текущую spell card
   - Получить / изменить способность управления временем (или улучшить имеющуюся)

Игрок гибко настраивает билд в течение забега, комбинируя ножи, spell cards и силы времени.

### Враги
Много, подразделяются на виды. Массовые столкновения требуют пространственного индексирования.

---

## Критерии MVP (20 дней)
- **Цель:** 1 полноценная арена (волна) из 3 фаз нарастающей сложности.
- **Оптимизация:** >= 60 FPS при 1000+ объектов, коллизии <= 5 мс.
- **Обязательные алгоритмы:** Sparse Set, Spatial Hash, Ring Buffer, Sweep & Prune, Persistent Snapshots, Rollback DSU.
- **Сохранение:** Прогресс забега в JSON.
- **Механики:** Глобальное/локальное управление временем (`local_time_scale`), откаты времени (Rewind через Undo-событий), 3 типа ножей (Normal, Delayed, Reflective).
- **Rewind:** работает без поломки логики игры и крашей.
- **UI:** главное меню («Начать игру», «Настройки», «Выход»), полный цикл: меню → арена → прокачка (выбор 1 из 3 улучшений) → следующая арена → смерть/победа → меню.
- **Визуальная обратная связь:** смена оттенка экрана, замедление анимаций спрайтов при временных эффектах.
- **Исключено из MVP:** Timeline Fracture (ветвление), сложная генерация уровней, мультиплеер, сюжет.

---

## Дорожная карта до MVP для показа (актуальная, 2026-06-21)

Фундамент (ECS, game loop, spatial hash) и базовый геймплей готов. Rewind готов.
Оставшиеся задачи по приоритету для закрытия MVP:

1. **TimeSystem** (`src/systems/time_system.py`) — Фаза 2
   - Time Stop (Space): всем кроме игрока `TimeAffected.scale=0`
   - Slow (LShift): `scale=0.3` для врагов/ножей
   - Drain TimeMana, режимы NORMAL/SLOW/TIME_STOP/REWINDING
   - Запуск ДО MovementSystem
2. **WaveSpawner** (`src/systems/spawner_system.py`)
   - Бесконечный спавн волн по краям экрана, рост сложности со временем
   - Параметры в `config/config_params.py` (интервал, размер пачки, типы)
3. **2 Spell Cards** (мана) — `src/systems/spell_card_system.py`
   - "Knives Around": спавн кольца ножей вокруг игрока
   - "Teleport": мгновенный перенос игрока на курсор
   - Клавиши Q/E (или иные), трата Mana, кулдаун
4. **ProgressionSystem** (`src/systems/progression_system.py`)
   - Враги при смерти дропают XP + мана (pickup или мгновенно)
   - Level-up при `current >= to_next` → пауза + draft 1-of-3
   - Upgrade registry: +урон ножа, +скорость атаки, +max HP, +скорость движения и т.д.
5. **UI + спрайты** (`src/ui/`, `src/rendering/`)
   - HUD: HP/Mana/TimeMana/уровень/режим времени
   - Спрайты вместо кругов (Сакуя, враги, ножи, босс)
   - Draft-оверлей при level-up
6. **Музыка / звук** (`src/audio/`) — pygame.mixer, фоновая музыка + sfx
7. **1 Босс** (`src/systems/boss_system.py` / компонент Boss)
   - Фазы боя, спец-атаки (спавн проджектайлов, призыв миньонов)
   - Спавн по таймеру/уровню — финал MVP-забега
8. **MVP для показа готов** 🎯

---

## Архитектура ядра

**Главная идея: НЕ хранить "состояние мира". Хранить timeline + deterministic simulation.**

`State(t) = Replay(Events[0..t])` — с оптимизациями (snapshots + Undo для обратного отката).

### ECS через Sparse Set для обработки объектов
Используется ООП-архитектура; ECS применяется как метод пакетной обработки больших массивов объектов.

Причина: десятки тысяч ножей, постоянный spawn/despawn, плотная итерация.

Sparse set даёт: cache locality, O(1) add/remove.

**Компоненты:** Position, Velocity, Knife, Enemy, TimeAffected, Collider, Health, Mana, TimeMana, Experience, Reflective, Frozen, TimelineAnchor

**Делать:** ECS для данных объектов. ООП/SOLID применяется к системам, модулям и общей архитектуре проекта.

---

## Иерархия сущностей (ECS Archetypes)

В ECS нет наследования. Entity = набор компонентов. Архетип = уникальная комбинация компонентов.
Ниже — все планируемые архетипы сущностей и их компонентный состав.

### Компоненты (справочник)

| Компонент | Поля | Назначение | Реализован |
|-----------|------|------------|------------|
| Position | x, y | Координаты в мире | ✅ |
| Velocity | x, y | Скорость (единиц/тик) | ✅ |
| Collider | radius | Круговой коллайдер | ✅ |
| Health | value, max_value | Здоровье | ✅ |
| Mana | value, max_value | Мана для spell cards | ✅ |
| TimeMana | value, max_value | Мана для способностей времени | ✅ |
| TimeAffected | scale | Локальный timescale (1.0=normal, 0.0=stopped, -1.0=reverse) | ✅ |
| TimelineAnchor | timeline_id | К какой timeline принадлежит | ❌ |
| Frozen | remaining_ticks | Сколько тиков ещё заморожен | ❌ |
| Owner | entity | Кто создал (нож → владелец) | ✅ |
| Lifetime | remaining_ticks | До самоуничтожения | ✅ |
| Knife | knife_type, damage, speed | Тип ножа, урон, скорость | ✅ |
| Reflective | bounces_remaining | Сколько рикошетов осталось | ✅ |
| Delayed | activate_ticks | Сколько тиков до активации | ✅ |
| Piercing | pierces_remaining | Сколько врагов может пробить | ❌ |
| Orbiting | center_entity, angle, angular_speed | Вокруг чего вращается | ❌ |
| TimeAnchored | (пустой маркер) | Игнорирует global time stop | ❌ |
| Recursive | trajectory: list[Position] | Помнит траекторию, не откатывается при rewind | ❌ |
| Player | (пустой маркер) | Маркер игрока | ✅ |
| Experience | level, current, to_next | Текущий опыт, уровень, опыт до следующего уровня | ✅ |
| Enemy | enemy_type, ai_state | Тип врага, состояние ИИ | ✅ |
| Boss | phase | Фаза босса | ❌ |
| SpellCard | spell_type, remaining_ticks, cooldown | Тип спелла, оставшееся время, кд | ❌ |
| TimeBubble | center_x, center_y, radius, scale, falloff | Параметры временного пузыря | ❌ |
| Projectile | damage, owner_id | Универсальный проджектайл (вражеский) | ❌ |
| Sprite | texture_id, layer | Что рисовать, слой отрисовки | ❌ |
| Animation | current_frame, frame_timer | Текущий кадр анимации | ❌ |
| CollisionFilter | layer, mask | Битовые слои коллизий | ✅ |
| InputState | mouse_x, mouse_y, mouse_pressed, keys_pressed | Состояние ввода (компонент) | ✅ |
| KnifeLoadout | current, available, cooldown | Выбор типа ножа игроком | ✅ |

### Архетипы (сущности игры)

#### Игрок

| Сущность | Компоненты |
|----------|------------|
| Сакуя (player) | Position, Velocity, Collider, Health, Mana, TimeMana, Experience, TimeAffected, TimelineAnchor, Player, Sprite, Animation |

#### Ножи

| Сущность | Компоненты |
|----------|------------|
| Normal Knife | Position, Velocity, Collider, Knife(normal), Lifetime, Owner, TimeAffected, CollisionFilter, Sprite |
| Delayed Knife | Position, Velocity(scale=0), Collider, Knife(delayed), Delayed, Lifetime, Owner, TimeAffected, CollisionFilter, Sprite |
| Reflective Knife | Position, Velocity, Collider, Knife(reflective), Reflective, Lifetime, Owner, TimeAffected, CollisionFilter, Sprite — отражение обрабатывает KnifeBounceSystem (после Collision+Combat) |
| Orbiting Knife | Position, Knife(orbiting), Orbiting, Collider, Owner, TimeAffected, TimelineAnchor, Sprite |
| Piercing Knife | Position, Velocity, Collider, Knife(piercing), Piercing, Lifetime, Owner, TimeAffected, TimelineAnchor, Sprite |
| TimeAnchored Knife | Position, Velocity, Collider, Knife(time_anchored), TimeAnchored, Lifetime, Owner, Sprite |
| Recursive Knife | Position, Velocity, Collider, Knife(recursive), Recursive, Lifetime, Owner, TimelineAnchor, Sprite |

#### Враги

| Сущность | Компоненты |
|----------|------------|
| Враг (базовый) | Position, Velocity, Collider, Health, Enemy, TimeAffected, TimelineAnchor, Sprite, Animation |
| Boss | Position, Velocity, Collider, Health, Enemy, Boss, TimeAffected, TimelineAnchor, Sprite, Animation |

#### Spell Cards & Time Effects

| Сущность | Компоненты |
|----------|------------|
| Spell Card | Position, SpellCard, TimeAffected, TimelineAnchor, Sprite |
| Time Bubble | Position, TimeBubble, Lifetime, TimeAffected, TimelineAnchor, Sprite |

#### Прочее

| Сущность | Компоненты |
|----------|------------|
| Вражеский проджектайл | Position, Velocity, Collider, Projectile, Lifetime, TimeAffected, TimelineAnchor, Sprite |
| Pickup (здоровье/мана/мана времени/опыт) | Position, Collider, Lifetime, Sprite |

### Сводка: какие компоненты у каких сущностей

```
                      Pos  Vel  Col  HP  Mana TMana Exp  Time  TL  Knife  Enemy  Player  Sprite  ...
Сакуя                 +    +    +   +    +    +    +     +    +    -      -      +      +
Normal Knife          +    +    +   -    -    -     +    +    +      -      -      +
Delayed Knife         +    -    +   -    -    -     +    +    +      -      -      +
Reflective Knife      +    +    +   -    -    -     +    +    +      -      -      +
Orbiting Knife        +    -    +   -    -    -     +    +    +      -      -      +
Piercing Knife        +    +    +   -    -    -     +    +    +      -      -      +
TimeAnchored Knife    +    +    +   -    -    -     -    -    +      -      -      +
Recursive Knife       +    +    +   -    -    -     +    +    +      -      -      +
Enemy                 +    +    +   +    -    -     +    +    -      +      -      +
Boss                  +    +    +   +    -    -     +    +    -      +      -      +
Enemy Projectile      +    +    +   -    -    -     +    +    -      -      -      +
Time Bubble           +    -    -   -    -    -     +    +    -      -      -      +
Pickup                +    -    +   -    -    -     -    -    -      -      -      +
```

**Примечание:** TimeAnchored Knife — единственная сущность без TimeAffected и TimelineAnchor (игнорирует глобальное время).

### Generation Handles
Обязательны для rewind — иначе сломаются ссылки.

```
Entity = { id: uint32, generation: uint32 }
```

### Fixed Tick Simulation
tick = 1/120 sec. Никакого delta-time. Rewind требует детерминизма и воспроизводимости.

### Ring Buffer Snapshot System
Храним: snapshots каждые N тиков (30) + event log с Undo-операциями между ними.
Rewind: найти ближайший snapshot (>= target) → восстановить → replay событий в обратном порядке (Undo).

### Command / Event Log (с Undo)
Все действия — события с парной Undo-операцией: SpawnKnife/UndoSpawnKnife, KnifeBounce/UndoKnifeBounce, FreezeArea/UndoFreezeArea, EnemyKilled/UndoEnemyKilled, TimeStopStart/UndoTimeStopEnd, ...
При Rewind события откатываются в обратном порядке (Tick N → Tick M).

### Selective Rewind
Не все объекты откатываются одинаково:
| Object | Rewind? |
|--------|---------|
| enemy | yes |
| boss | partial |
| anchored knife | no |
| player | selectable |

Нужен `TimelineLayer`.

### Spatial Hash Grid
cell → entities. Ускоряет: collision, AoE, time fields, knife lookup.

---

## Алгоритмы и структуры данных

### MUST HAVE
| Алгоритм | Где |
|----------|-----|
| Sparse Set | ECS |
| Spatial Hash | collision |
| Ring Buffer | rewind snapshots |

> **Примечание:** Event Log (с Undo) и Fixed Tick (1/120) — архитектурные компоненты, а не алгоритмы (см. раздел «Архитектура ядра»).

### STRONG (продвинутая оптимизация)
| Алгоритм | Где | Приоритет |
|----------|-----|-----------|
| Persistent snapshots | rewind | **ВЫСОКИЙ (MVP)** |
| Sweep & Prune | collision | **ВЫСОКИЙ (MVP)** |

### ICPC-level (дополнительные механики)
| Алгоритм | Где | Приоритет |
|----------|-----|-----------|
| Rollback DSU | topology / стаи врагов | **ВЫСОКИЙ (MVP)** |
| SAT collision | сложные ножи | Низкий |

---

## Ключевая проблема и решение

**Проблема:** одновременно очень много объектов + time mechanics + огромное число взаимодействий.

**Решение:** data-oriented ECS + sparse set + spatial hash + fixed tick + event sourcing + ring buffer snapshots.

**Самая интересная часть:** selective temporal consistency — какие объекты подчиняются времени, какие существуют вне времени (time-anchored ножи), какие «помнят» позицию вопреки откату (recursive ножи). Это механика уровня Braid + Touhou + simulation sandbox.

---

## Правила работы с PROGRESS.md

- **PROGRESS.md** — живой документ, отражающий реальное состояние проекта на момент последней проверки
- **Обновляется** по запросу пользователя: я сканирую проект, сверяю файлы с планом и обновляю статусы
- **Статусы:** ✅ Готов | ⚠️ Частично | ❌ Не начат | ❓ Неясно
- **Секции:**
  - Инфраструктура — сборка, структура, конфиги
  - Фазы 1–4 — реализация по плану (каждая фаза зависит от предыдущей)
  - Проблемы — что сломано или требует внимания
  - Следующие шаги — приоритизированный список того, что делать дальше
- **Фазы привязаны к архитектуре из PLAN:** Фаза 1 = фундамент (ECS, loop, spatial hash), Фаза 2 = время (events, snapshots, rewind, time domains), Фаза 3 = геймплей (ножи, спеллы, враги, игрок), Фаза 4 = продвинутые механики (timeline fracture и др.)
- **Правило:** ни один статус не ставится ✅ без реального кода в проекте

---

*Файл ведётся как живой документ — обновляется по мере развития проекта.*
