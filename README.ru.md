# ETS2Mods

Три личных мода для одиночной игры Euro Truck Simulator 2 (сделаны под версию 1.61.1.1) и маленький распаковщик архивов SCS HashFS.

| Файл мода | Название в игре | Что делает |
|---|---|---|
| `alexey_no_fines.scs` | No Fines (Alexey) | Все штрафы полиции и камер равны 0, нарушения не засчитываются. Нет штрафа за отказ от груза, повреждение груза не уменьшает оплату, при опоздании рейс остаётся в силе 30 дней. |
| `alexey_more_traffic.scs` | More Traffic (Alexey) | Поднимает общий лимит машин ИИ до 300. Саму плотность задаёт `g_traffic` в `config.cfg`. |
| `alexey_money.scs` | Big Money (Alexey) | Оплата рейсов примерно в 10 раз выше. Новый профиль начинает с 10 000 000 €. Внутри также экономическая часть No Fines. |

Оригинальных файлов SCS в репозитории нет. `tools/build_mods.py` берёт их из установленной игры, меняет только перечисленные значения и собирает моды. Если обновление игры переименует параметр, сборка остановится с ошибкой и не выпустит сломанный мод.

## Что поменяно

| Файл | Параметр | Было | Стало |
|---|---|---|---|
| def/police_data.sii | fine_factor_base | 0.2 | 0.0 |
| def/police_data.sii | fine_factor_step | 0.08 | 0.0 |
| def/police_data.sii | fine_amounts[0..13] | от 100 до 2000 | 0 |
| def/police_data.sii | offence_probabilty[0..13] | от 0.0 до 1.0 | 0.0 |
| def/police_data.sii | offence_police_probabilty[0..13] | от 0.3 до 1.0 | 0.0 |
| def/economy_data.sii | abandoned_job_fine | 12000 | 0 |
| def/economy_data.sii | cargo_damage_cost | 5.0 | 0.0 |
| def/economy_data.sii | cargo_damage_cost_factor | 0.04 | 0.0 |
| def/economy_data.sii | late_delivery_max_overtime[0..2] | 2880 / 720 / 240 мин | 43200 мин (30 дней) |
| def/economy_data.sii | revenue_per_km_base | 15 | 150 (только Big Money) |
| def/economy_data.sii | fixed_revenue | 600 | 6000 (только Big Money) |
| def/initial_save/normal/game.sii | money_account | 2000 | 10000000 (только Big Money) |
| def/traffic_data.sii | max_vehicle_count | не задан (в комментарии 50) | 300 |
| config.cfg (папка пользователя) | g_traffic | 1.0 | 3.0 |
| config.cfg (папка пользователя) | g_developer / g_console | 0 / 0 | 1 / 1 |

Все имена взяты из файлов самой игры. Команда консоли и диапазон `g_traffic` (от 0 до 10) проверены по строкам `eurotrucks2.exe`.

## Порядок модов

В Менеджере модов побеждает тот мод, который стоит выше в списке активных. No Fines и Big Money оба заменяют `def/economy_data.sii`, поэтому **Big Money ставить выше No Fines**. В Big Money уже есть экономические правки No Fines, так что при таком порядке ничего не теряется. Все три ставить выше модов из Мастерской, которые трогают те же файлы (плотность трафика, отмена штрафов и т.п.).

## Плотность трафика

`g_traffic` - это множитель. Штатно 1.0, игра принимает от 0.0 до 10.0. 3.0 - спокойный старт. 4-5 в больших городах уже очень много и съедает FPS. Менять можно в консоли прямо в игре (`g_traffic 4`) или в `config.cfg`, когда игра закрыта.

## Деньги через консоль

В `config.cfg` включены `g_developer "1"` и `g_console "1"`. Рядом лежит копия оригинала `config.cfg.2026-10-02.bak`. В игре консоль открывается клавишей `~` (под Esc). Команда:

```
cheat money 1000000
```

Подсказка из самой игры: `cheat money [amount] [set]`.

## Пересборка после обновления игры

```
python tools/build_mods.py --install
```

Скрипт прочитает новый `def.scs`, возьмёт версию из `version.scs` для `compatible_versions` и положит моды в `Documents\Euro Truck Simulator 2\mod`. Значения меняются в `mods/<имя>/mod.json`. Иконки перерисовать: `.venv\Scripts\python tools\make_icons.py` (нужен Pillow: `pip install -r tools/requirements.txt` в venv).

## Распаковщик HashFS

`tools/hashfs.py` читает архивы HashFS v1 и v2, нужна только стандартная библиотека Python:

```
python tools/hashfs.py ls      <архив.scs> def
python tools/hashfs.py tree    <архив.scs> def/country
python tools/hashfs.py cat     <архив.scs> def/economy_data.sii
python tools/hashfs.py extract <архив.scs> extracted def/police_data.sii def/initial_save
```

Грабля: пути хэшируются **CityHash64 версии 1.0.x**. Пакет `cityhash` из PyPI - это версия 1.1, хэши у него другие. Совпадает он только для пустого пути корня, и это сбивает с толку. Поэтому в `tools/cityhash103.py` своя реализация 1.0.x на чистом Python. Подробности формата - в английском README.

Не для TruckersMP и не для Конвоя. Это моды только для одиночной игры.
