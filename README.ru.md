# EuroTrackMyMods

Личные моды для одиночной игры Euro Truck Simulator 2 (сделаны под версию 1.61.1.1) и маленькие инструменты: распаковщик HashFS, правка денег в сохранении и проверка консольных команд.

| Файл мода | Название в игре | Что делает |
|---|---|---|
| `alexey_money.scs` | Big Money (Alexey) | Оплата рейсов примерно в 10 раз выше. Новый профиль начинает с 10 000 000 €. Внутри также экономические правки Free Services и No Fines. |
| `alexey_free_services.scs` | Free Services (Alexey) | Бесплатное топливо, паромы и поезд через Ла-Манш, вызов помощи и эвакуация, экстренная заправка и зарядка, восстановление износа. Внутри также экономические правки No Fines. |
| `alexey_no_fines.scs` | No Fines (Alexey) | Все штрафы полиции и камер равны 0, нарушения не засчитываются. Нет штрафа за отказ от груза, повреждение груза не уменьшает оплату, при опоздании рейс в силе 30 дней. |
| `alexey_no_damage.scs` | No Damage (Alexey) | Грузовик и прицеп не получают урон, нет износа, груз не повреждается. |
| `alexey_more_traffic.scs` | More Traffic (Alexey) | Поднимает общий лимит машин ИИ до 300. Саму плотность задаёт `g_traffic` в `config.cfg`. |

Оригинальных файлов SCS в репозитории нет. `tools/build_mods.py` берёт их из установленной игры, меняет только перечисленные значения и собирает моды. Если обновление переименует параметр, сборка остановится с ошибкой.

## Порядок модов

Подсказка самой игры в Менеджере модов: «Приоритет модов определяется их положением в списке активных модов». Самый верхний - самый главный.

Сверху вниз:

1. Big Money (Alexey)
2. Free Services (Alexey)
3. No Fines (Alexey)
4. No Damage (Alexey)
5. More Traffic (Alexey)
6. всё остальное

Big Money, Free Services и No Fines все заменяют `def/economy_data.sii`. В каждом, кто выше по списку, уже есть экономические правки тех, кто ниже, поэтому при таком порядке ничего не теряется. Обратная сторона: Big Money в одиночку тоже даёт бесплатную эвакуацию и отменяет штраф за отказ от груза.

Моды из Мастерской, которые заменяют те же файлы (проверено в папке Мастерской):

| Мод Мастерской | Файл | Что делать |
|---|---|---|
| Speeding ticket removal (1248269969) | def/police_data.sii | Убирает только штрафы за скорость. Держать ниже No Fines или выключить. |
| No Damage от rasmusolle (1724816341) | def/damage_data.sii | То же, что наш No Damage. Оставить один. |
| Brutal Traffic (3103116974) | def/traffic_data.sii | max_vehicle_count 4500 и поведение ИИ. Работает только один traffic_data. |
| Real Traffic Density (1236032431) | def/traffic_data.sii | max_vehicle_count 500 и дистанции появления машин. |

## Что поменяно

Полные таблицы (файл, параметр, было, стало) - в английском README. Коротко:

- No Fines: police_data.sii - все fine_amounts, offence_probabilty, offence_police_probabilty и fine_factor равны 0. economy_data.sii - abandoned_job_fine 12000 -> 0, cargo_damage_cost 5.0 -> 0, cargo_damage_cost_factor 0.04 -> 0, late_delivery_max_overtime -> 43200 мин.
- No Damage: damage_data.sii - truck_damage_coef и trailer_damage_coef 0.0007 -> 0, dragged_trailer_damage_coef 0.00002 -> 0, truck_to_trailer_dmg 0.2 -> 0, cargo_damage_ratio 1.0 -> 0, весь износ (engine/transmission/wheel/trailer_wheel, обычный и unfixable) -> 0.
- Free Services: economy_data.sii - tow_price_base 150 -> 0, tow_price_factor 0.4 -> 0, refuel_price_base 150 -> 0, refuel_price_factor 3 -> 0, recharge_price_base 150 -> 0, recharge_price 2 -> 0. service_data.sii - restore у грузовика и прицепа 1000 и 1.1 -> 0. fuel_price во всех 36 странах -> 0. price на всех 19 переправах -> 0.
- Big Money: revenue_per_km_base 15 -> 150, fixed_revenue 600 -> 6000, стартовые деньги 2000 -> 10 000 000.
- More Traffic: max_vehicle_count 300. config.cfg: g_traffic 3.0, g_developer 1, g_console 1, g_save_format 2.

## Что не поменяно и почему

- Платные дороги. Цены пунктов оплаты лежат в данных карты, а не в def-файлах. В exe есть поле экономики `toll_fees`, но его тип и смысл по файлам игры не проверить, поэтому не трогал. То же с `truck_scales_cost` и `oversize_job_cancel_cost`.
- Ремонт уже полученных повреждений. Цена считается в коде по стоимости деталей. С No Damage новых повреждений нет.
- Быстрое перемещение. Отдельного параметра цены в def-файлах нет. Вызов помощи (эвакуация) покрыт `tow_price_*`.

## Деньги: команды `cheat` в 1.61 нет

`cheat money 1000000` отвечает `unknown command` даже при `g_developer 1` и `g_console 1`. `tools/exe_console_commands.py` показывает 83 описания команд в `eurotrucks2.exe`. 79 из них игра регистрирует. Не регистрируются 4: `cheat` и три команды профайлера. Значит, никакая настройка или параметр запуска `cheat` в этой сборке не включит.

Что работает вместо:

1. Big Money: каждый рейс оплачивается примерно в 10 раз выше.
2. `tools/save_money.py` меняет деньги в сохранении. Сначала закрыть игру.

```
python tools/save_money.py                                       # список сохранений и денег
python tools/save_money.py --save autosave --set 50000000        # пробный прогон, без записи
python tools/save_money.py --save autosave --set 50000000 --apply
python tools/save_money.py --save autosave --restore             # вернуть из резервной копии
```

Скрипт читает обычные зашифрованные сохранения (ScsC + BSII) и текстовые. Перед записью копирует папку сохранения в `Documents\Euro Truck Simulator 2\save_backups\`. Бинарное сохранение записывается обратно как BSII без шифрования, текстовое правится на месте. В `config.cfg` стоит `g_save_format "2"`, поэтому новые сохранения будут текстовыми.

## Пересборка после обновления игры

```
python tools/build_mods.py --install
```

Значения меняются в `mods/<имя>/mod.json`. В имени файла можно писать `*`, например `def/country/*.sui`. Иконки: `.venv\Scripts\python tools\make_icons.py`. Пакеты Python для инструментов перечислены в `tools/requirements.txt`, ставить в venv.

Не для TruckersMP и не для Конвоя. Это моды только для одиночной игры.
