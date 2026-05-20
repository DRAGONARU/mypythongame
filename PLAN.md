# PLAN — Игровой проект УрФУ

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

### Ножи (Knife System)
| Тип | Поведение |
|-----|-----------|
| Normal | стандартный проджектайл |
| Delayed | стоит на месте (timescale=0), потом активируется (timescale=1) |
| Reflective | рикошет от поверхностей |
| Orbiting | вращение вокруг цели |
| Piercing | проходит через врагов |
| TimeAnchored | игнорирует global time stop |
| Recursive | при rewind не откатывается, сохраняет trajectory memory |

Атаки: удар ножом (melee), бросок (projectile).

### Манипуляции со временем
| Эффект | scale | Область |
|--------|-------|---------|
| normal | 1.0 | глобально |
| slow | 0.2 | глобально / радиус |
| fast | 3.0 | глобально / радиус |
| stopped | 0.0 | глобально / радиус |
| reverse | -1.0 | rewind |

**Time Bubble** — spell card создаёт: center, radius, timescale, falloff.
Каждый объект имеет `local_time_scale`. Обновление: `position += velocity * dt * local_time_scale`.

### Spell Cards
Event-driven: OnTick, OnHit, OnFreeze, OnRewind, OnTimeStop.

### Timeline Fracture (ветвление timelines)
Rewind не удаляет старую timeline. Каждая entity имеет `timeline_id`.
Можно: сражаться с прошлой версией себя, видеть старые ножи, накладывать timelines.

### Враги
Много, подразделяются на виды. Массовые столкновения требуют пространственного индексирования.

---

## Архитектура ядра

**Главная идея: НЕ хранить "состояние мира". Хранить timeline + deterministic simulation.**

`State(t) = Replay(Events[0..t])` — с оптимизациями (snapshots).

### Data-oriented ECS через Sparse Set
MUST HAVE. Причина: десятки тысяч ножей, постоянный spawn/despawn, плотная итерация.

Sparse set даёт: cache locality, O(1) add/remove.

**Компоненты:** Position, Velocity, Knife, Enemy, TimeAffected, Collider, Health, Reflective, Frozen, TimelineAnchor

**НЕ делать:** inheritance-heavy, virtual update() everywhere.
**Делать:** data-oriented ECS. ООП/SOLID применяется к системам и модулям, не к каждой entity.

---

## Иерархия сущностей (ECS Archetypes)

В ECS нет наследования. Entity = набор компонентов. Архетип = уникальная комбинация компонентов.
Ниже — все планируемые архетипы сущностей и их компонентный состав.

### Компоненты (справочник)

| Компонент | Поля | Назначение |
|-----------|------|------------|
| Position | x, y | Координаты в мире |
| Velocity | x, y | Скорость (единиц/тик) |
| Collider | radius | Круговой коллайдер |
| Health | current, max | Здоровье |
| TimeAffected | scale | Локальный timescale (1.0=normal, 0.0=stopped, -1.0=reverse) |
| TimelineAnchor | timeline_id | К какой timeline принадлежит |
| Frozen | remaining_ticks | Сколько тиков ещё заморожен |
| Owner | entity_id | Кто создал (нож → владелец) |
| Lifetime | remaining_ticks | До самоуничтожения |
| Knife | knife_type, damage, speed | Тип ножа, урон, скорость |
| Reflective | bounces_remaining | Сколько рикошетов осталось |
| Delayed | activate_tick | На каком тике активироваться |
| Piercing | pierces_remaining | Сколько врагов может пробить |
| Orbiting | center_entity, angle, angular_speed | Вокруг чего вращается |
| TimeAnchored | (пустой маркер) | Игнорирует global time stop |
| Recursive | trajectory: list[Position] | Помнит траекторию, не откатывается при rewind |
| Player | (пустой маркер) | Маркер игрока |
| Enemy | enemy_type, ai_state | Тип врага, состояние ИИ |
| Boss | phase | Фаза босса |
| SpellCard | spell_type, remaining_ticks, cooldown | Тип спелла, оставшееся время, кд |
| TimeBubble | center_x, center_y, radius, scale, falloff | Параметры временного пузыря |
| Projectile | damage, owner_id | Универсальный проджектайл (вражеский) |
| Sprite | texture_id, layer | Что рисовать, слой отрисовки |
| Animation | current_frame, frame_timer | Текущий кадр анимации |

### Архетипы (сущности игры)

#### Игрок

| Сущность | Компоненты |
|----------|------------|
| Сакуя (player) | Position, Velocity, Collider, Health, TimeAffected, TimelineAnchor, Player, Sprite, Animation |

#### Ножи

| Сущность | Компоненты |
|----------|------------|
| Normal Knife | Position, Velocity, Collider, Knife(normal), Lifetime, Owner, TimeAffected, TimelineAnchor, Sprite |
| Delayed Knife | Position, Collider, Knife(delayed), Delayed, Owner, TimeAffected, TimelineAnchor, Sprite |
| Reflective Knife | Position, Velocity, Collider, Knife(reflective), Reflective, Lifetime, Owner, TimeAffected, TimelineAnchor, Sprite |
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
| Pickup (здоровье/буст) | Position, Collider, Lifetime, Sprite |

### Сводка: какие компоненты у каких сущностей

```
                     Pos  Vel  Col  HP  Time  TL  Knife  Enemy  Player  Sprite  ...
Сакуя                 +    +    +   +    +    +    -      -      +      +
Normal Knife          +    +    +   -    +    +    +      -      -      +
Delayed Knife         +    -    +   -    +    +    +      -      -      +
Reflective Knife      +    +    +   -    +    +    +      -      -      +
Orbiting Knife        +    -    +   -    +    +    +      -      -      +
Piercing Knife        +    +    +   -    +    +    +      -      -      +
TimeAnchored Knife    +    +    +   -    -    -    +      -      -      +
Recursive Knife       +    +    +   -    +    +    +      -      -      +
Enemy                 +    +    +   +    +    +    -      +      -      +
Boss                  +    +    +   +    +    +    -      +      -      +
Enemy Projectile      +    +    +   -    +    +    -      -      -      +
Time Bubble           +    -    -   -    +    +    -      -      -      +
Pickup                +    -    +   -    -    -    -      -      -      +
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
Храним: snapshots каждые N тиков (30) + event log между ними.
Rewind: найти ближайший snapshot → пересимулировать.

### Command / Event Log
Все действия — события: SpawnKnife, KnifeBounce, FreezeArea, EnemyKilled, TimeStopStart, TimeStopEnd, ...

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
| Event Log | replay |
| Fixed Tick (1/120) | determinism |

### STRONG (желательно)
| Алгоритм | Где |
|----------|-----|
| Persistent snapshots | rewind |
| Zobrist Hash | state dedup |
| Sweep & Prune | collision |
| Bitset SIMD | массовые статусы |

### ICPC-level (если будет время)
| Алгоритм | Где |
|----------|-----|
| Rollback DSU | topology |
| Persistent DAG | timelines |
| SAT collision | сложные ножи |

---

## Ключевая проблема и решение

**Проблема:** одновременно очень много объектов + time mechanics + огромное число взаимодействий.

**Решение:** data-oriented ECS + sparse set + spatial hash + fixed tick + event sourcing + ring buffer snapshots.

**Самая интересная часть:** selective temporal consistency — какие объекты подчиняются времени, какие существуют вне времени, какие «помнят» прошлые timelines. Это механика уровня Braid + Touhou + simulation sandbox.

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
