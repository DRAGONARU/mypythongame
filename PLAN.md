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

*Файл ведётся как живой документ — обновляется по мере развития проекта.*
