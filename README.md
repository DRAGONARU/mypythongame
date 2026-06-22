# Project: Luna dial survivors

## Description

Моя игра по проге, с применением различных алгоритмов и структур данных.

## Запуск

Чтобы запустить игру, надо выполнить файл main.py в корне.

## Установка

Требования
Python 3.13 или новее (скачать)
pip (идёт в комплекте с Python)
ОС: Windows / macOS / Linux
Дисплей и аудио (Pygame использует SDL2 — виртуальные дисплеи/VPS без GPU не подойдут)
Установка
1. Склонировать репозиторий
git clone <url-репозитория> gaming_project_urfu
cd gaming_project_urfu
Либо распаковать архив с проектом и открыть терминал в папке проекта.

2. Создать виртуальное окружение (рекомендуется)
Windows (PowerShell):

python -m venv .venv
.\.venv\Scripts\Activate.ps1
Если PowerShell блокирует запуск скрипта, разрешите один раз:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
macOS / Linux:

python3 -m venv .venv
source .venv/bin/activate
После активации в начале строки появится (.venv).

3. Установить пакет в editable-режиме
python -m pip install --upgrade pip
pip install -e .
Это установит:

зависимость pygame>=2.5
сам пакет проекта (src/, config/) в режиме редактирования — импорты from src... и from config... будут работать из любого каталога.
4. (Опционально) Установить dev-зависимости
pip install -e ".[dev]"
Добавит pytest и pytest-cov для запуска тестов.

Запуск игры
python main.py
Откроется окно «Luna Dial Survivors» (800×600). Музыка заиграет, если в assets/ есть соответствующие файлы.

Ассеты
Игра ищет ассеты в папке assets/:

Файл	Назначение	Что если отсутствует
assets/2160.png	Тайловый фон	Заливка цветом BG_COLOR
assets/music.mp3	Фоновая музыка	Тишина (fallback без ошибки)
assets/boss_music.mp3	Музыка босса	Продолжит играть обычный трек
assets/sheet.png	Спрайты игрока/ножа	Процедурные круги
assets/enemy_sprites.png	Спрайты врага/босса	Процедурные круги
Если папки assets/ нет или файлы отсутствуют — игра всё равно запустится с процедурной графикой и без звука.

Управление
Клавиша / мышь	Действие
WASD	Движение игрока
ЛКМ (удерживать)	Бросок ножей в сторону курсора
ПКМ	Спелл-карта (по кулдауну)
Z	Смена спелл-карты (knives/teleport)
1 / 2 / 3	Смена типа ножа (normal/delayed/reflective)
E (удерживать)	Slow — замедление времени
Space (удерживать)	Time Stop — остановка времени
R (удерживать)	Rewind — перемотка назад
ESC / Q	Выход из игры
Запуск тестов
pytest
Или с покрытием:

pytest --cov=src --cov-report=term-missing
Частые проблемы
No module named 'src' — пакет не установлен в editable-режиме. Выполните pip install -e . из корня проекта.

No module named 'pygame' — зависимости не установлены. Выполните pip install -e ..

Окно не открывается / pygame.error: No available video device — запуск на сервере без дисплея. Pygame требует GUI-окружение; используйте локальную машину или VNC.

Музыка не играет — отсутствуют assets/music.mp3 / assets/boss_music.mp3. Это нормально, игра работает без звука.

PowerShell: Activate.ps1 cannot be loaded — выполните Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass и повторите активацию виртуального окружения.

