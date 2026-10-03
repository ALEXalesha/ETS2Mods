# ETS2Mods - моды OpenRoad для Euro Truck Simulator 2

Десять модов для одиночной игры Euro Truck Simulator 2 (версия 1.61) и инструменты, которые собирают их из файлов самой игры: распаковщик HashFS, правка денег, уровня и навыков в сохранении, тесты.

> Проект не связан с SCS Software и не одобрен ею. «Euro Truck Simulator 2» - товарный знак SCS Software. Моды фанатские, только для одиночной игры; в TruckersMP и Конвое они не работают.

| Мод (файл в выпуске) | Что делает |
|---|---|
| OpenRoad: Hyper Power (`OpenRoad_Hyper_Power.scs`) | Безумный: момент x12, главная пара x0.35 (потолок около 460-590 км/ч), почти нет сопротивления воздуха, сцепление +30%, тормоза x4. Вместо Super Power. |
| OpenRoad: Super Power (`OpenRoad_Super_Power.scs`) | Момент x3, сопротивление воздуха вдвое меньше, тормоза x2. Управляемо. |
| OpenRoad: Big Money (`OpenRoad_Big_Money.scs`) | Оплата рейсов примерно x10; новый профиль начинает с 10 000 000 €. |
| OpenRoad: Free Services (`OpenRoad_Free_Services.scs`) | Топливо почти даром (0.0001 €/л), паромы и поезд бесплатно, бесплатные эвакуация, экстренная заправка и восстановление износа. |
| OpenRoad: No Sleep (`OpenRoad_No_Sleep.scs`) | Водитель не устаёт. |
| OpenRoad: No Fuel (`OpenRoad_No_Fuel.scs`) | Водитель не устаёт, двигатели тратят 1/10000 топлива. |
| OpenRoad: No Fines (`OpenRoad_No_Fines.scs`) | Нет штрафов полиции и камер, нет штрафа за отказ, повреждение груза не уменьшает оплату, 30 дней на опоздание. |
| OpenRoad: No Rollover (`OpenRoad_No_Rollover.scs`) | Передний стабилизатор в 3 раза жёстче; плюс ползунки устойчивости в настройках. |
| OpenRoad: No Damage (`OpenRoad_No_Damage.scs`) | Нет урона, износа и повреждения груза. |
| OpenRoad: More Traffic (`OpenRoad_More_Traffic.scs`) | Лимит машин ИИ 300; плотность - переменная игры `g_traffic`. |

## Установка

- **Мастерская Steam:** подписаться на моды OpenRoad и включить их в Менеджере модов.
- **Из выпусков:** скачать `.scs` из [последнего выпуска](../../releases/latest) и положить в `Документы\Euro Truck Simulator 2\mod`. Затем включить в Менеджере модов (профиль -> Менеджер модов) в порядке ниже.

## Порядок модов

Подсказка самой игры: «Приоритет модов определяется их положением в списке активных модов». Верхний - главный.

Сверху вниз (`mods/order.json`):

1. Hyper Power (или выключен, если нужен Super Power)
2. Super Power (выключить, если включён Hyper Power; ниже него он всё равно ничего не делает)
3. Big Money
4. Free Services
5. No Sleep
6. No Fuel
7. No Fines
8. No Rollover
9. No Damage
10. More Traffic
11. другие моды

Некоторые моды меняют один и тот же файл:
- `economy_data.sii` - Big Money, Free Services, No Sleep, No Fines;
- 203 файла двигателей - Hyper/Super Power, No Fuel;
- `physics.sii` - Hyper/Super Power, No Rollover.

Игра берёт только самую верхнюю копию, поэтому каждый мод несёт и правки модов ниже по списку - ничего не теряется. Hyper Power заменяет Super Power и его x3 не несёт. Обратная сторона: мод в одиночку приносит правки нижних в общих файлах. Например, Big Money в одиночку тоже даёт бесплатную эвакуацию.

## Что поменяно (файл, параметр, было, стало)

### No Fines
| Файл | Параметр | Было | Стало |
|---|---|---|---|
| police_data.sii | fine_factor_base / fine_factor_step | 0.2 / 0.08 | 0 / 0 |
| police_data.sii | fine_amounts[0..13] | 100-2000 | 0 |
| police_data.sii | offence_probabilty, offence_police_probabilty [0..13] | 0-1 | 0 |
| economy_data.sii | abandoned_job_fine | 12000 | 0 |
| economy_data.sii | cargo_damage_cost / _factor | 5.0 / 0.04 | 0 / 0 |
| economy_data.sii | late_delivery_max_overtime[0..2] | 2880 / 720 / 240 мин | 43200 мин |

### No Damage
| Файл | Параметр | Было | Стало |
|---|---|---|---|
| damage_data.sii | truck_damage_coef / trailer_damage_coef | 0.0007 | 0 |
| damage_data.sii | dragged_trailer_damage_coef | 0.00002 | 0 |
| damage_data.sii | truck_to_trailer_dmg | 0.2 | 0 |
| damage_data.sii | cargo_damage_ratio | 1.0 | 0 |
| damage_data.sii | engine/transmission/wheel_wear | 2e-6 | 0 |
| damage_data.sii | engine/transmission_wear_unfixable / wheel_wear_unfixable | 2e-7 / 2e-5 | 0 |
| damage_data.sii | trailer_wheel_wear / _unfixable | 2e-6 / 2e-5 | 0 |

### Free Services
| Файл | Параметр | Было | Стало |
|---|---|---|---|
| economy_data.sii | tow_price_base / tow_price_factor | 150 / 0.4 | 0 / 0 |
| economy_data.sii | refuel_price_base / refuel_price_factor | 150 / 3 | 0 / 0 |
| economy_data.sii | recharge_price_base / recharge_price | 150 / 2 | 0 / 0 |
| service_data.sii | truck/trailer_restore_accessory_fixed_price / _price_coef | 1000 / 1.1 | 0 / 0 |
| country/*.sui (36 стран) | fuel_price | 0.829-2.555 | 0.0001 |
| ferry/connection/*.sii (19 переправ) | price | 65-1212 | 0 |

Почему топливо 0.0001, а не 0. С нулём панель заправки показывала «Литров: -nan(ind)». В exe литры считаются как «стоимость / цена» без проверки на ноль; при цене 0 выходит 0/0 = NaN. Итог округляется до целых рублей/евро. При 0.0001 €/л полный бак 1000 л стоит 0,10 €, на экране это 0. Цена за литр показывается как минимальная копейка (около ₽0,01). Тест `tests/test_mods.py` падает, если где-то fuel_price ровно 0.

### No Sleep и No Fuel
С версии 1.1.0 это два отдельных мода (раньше был один общий).

| Мод | Файл | Параметр | Было | Стало |
|---|---|---|---|---|
| No Sleep | economy_data.sii | maximum_driving_time (мин) | 660 | 10000000 |
| No Fuel | truck/*/engine/*.sii (203 двигателя, 26 моделей) | consumption_coef | нет | 0.0001 (новая строка) |

`consumption_coef` в файлах игры не встречается. По таблице атрибутов в exe это float у `accessory_engine_data`, как `torque`. Ровно 0 не ставится по той же причине деления на ноль (средний расход и запас хода). Самый простой способ отключить сон без мода - снять галочку «Эмуляция усталости» в настройках (`g_fatigue`).

### Super Power
| Файл | Параметр | Было | Стало |
|---|---|---|---|
| truck/*/engine/*.sii (203 двигателя) | torque | 1300-3800 Нм | x3 (3900-11400) |
| то же | secondary_torque (где есть) | разный | x3 |
| vehicle/physics.sii | air_resistance | 3.0 | 1.5 |
| vehicle/physics.sii | brake_torque_factor | 1.0 | 2.0 |

Охвачены все 26 моделей игры и установленных DLC (DAF, Iveco, MAN, Mercedes, Renault, Scania, Volvo). Не охвачены грузовики из других модов и неустановленных DLC.

Что ограничивает скорость:
- Ограничитель скорости - это галочка в настройках (`g_use_speed_limiter`).
- Сопротивление воздуха. Сила = air_resistance x скорость²: половина сопротивления даёт примерно +26% скорости, мощность x3 - ещё примерно +44%.
- Передачи и обороты. Кривые момента кончаются около 2500 об/мин. При овердрайве 0.8, мосте 2.59 и колесе около 0.5 м это примерно 200-225 км/ч. «Бесконечной» скорости без правки коробок и кривых момента не бывает.

### Hyper Power
| Файл | Параметр | Было | Стало |
|---|---|---|---|
| truck/*/engine/*.sii (203 двигателя) | torque, secondary_torque | 1300-3800 Нм | x12 |
| truck/*/transmission/*.sii (170 коробок) | differential_ratio | 2.38-4.83 | x0.35 |
| vehicle/physics.sii | air_resistance | 3.0 | 0.1 (не ноль) |
| vehicle/physics.sii | brake_torque_factor / brake_cooling_rate | 1.0 / 0.01 | 4.0 / 0.05 |
| vehicle/physics.sii | steering_sensitivity_multiplier_minimum | 0.2 | 0.1 |
| f_tire, r_tire (31 шина) | grip_factor (по умолчанию в коде 1.0) | нет | 1.3 |

Hyper Power заменяет Super Power: правки No Fuel и No Rollover он несёт, а x3 от Super Power - нет.

Максимальная скорость посчитана по реальным числам (`python tools/top_speed.py`). Колесо 315/70 R22.5 - радиус 0.506 м. Обороты - конец кривой момента, в среднем 2200.

| | Общее передаточное (лучшее / среднее) | Потолок по передачам |
|---|---|---|
| Было | 2.020 / 2.620 | 208 / 160 км/ч |
| Hyper Power | 0.707 / 0.917 | около 590 / 460 км/ч |

Мощности хватает с запасом: воздух на 460 км/ч съедает около 0.2 МВт, а двигатель x12 даёт несколько МВт. Значит, потолок ставят передачи и конец кривой момента.

Что ещё ограничивает:
- Обороты и кривые момента я не растягивал: к ним привязаны точки переключения автомата, тахометр и звук.
- Шаг физики: на 130+ м/с машина пролетает больше 2 м за кадр, тонкие препятствия можно «проскочить».
- Подгрузка карты может не успевать.
- Стрелка спидометра в кабине упрётся в край, а цифры на HUD продолжат расти.

Жёсткого ограничения скорости в exe я не нашёл. ИИ-трафику скорость безразлична. Камеры без No Fines штрафуют.

На первой передаче момент на колёсах примерно x4.2 от стока. Пустой грузовик может буксовать, и тогда антипробуксовка срежет мощность. Больше сцепления - больше риск переворота в быстрых поворотах, поэтому держать No Rollover и ползунки устойчивости на максимуме.

### No Rollover
| Файл | Параметр | Было | Стало |
|---|---|---|---|
| vehicle/physics.sii | sway_bar_stiffness_factor (передний стабилизатор) | 1.0 | 3.0 |

Главное средство - в настройках, раздел «Геймплей»: «Устойчивость транспортного средства» (`g_truck_stability`) и «Устойчивость прицепа» (`g_trailer_stability`). По подсказке игры они опускают центр тяжести; поставить оба на максимум. Центр тяжести грузовика задают модели, а не def-файлы, поэтому «никогда не переворачивается» мод гарантировать не может.

### Big Money и прочее
| Файл | Параметр | Было | Стало |
|---|---|---|---|
| economy_data.sii | revenue_per_km_base / fixed_revenue | 15 / 600 | 150 / 6000 |
| initial_save/normal/game.sii | money_account | 2000 | 10000000 |
| traffic_data.sii | max_vehicle_count | нет (50) | 300 |
| config.cfg | g_traffic / g_developer / g_console / g_save_format | 1.0 / 0 / 0 / 0 | 3.0 / 1 / 1 / 2 |

## Правка сохранений (игра закрыта)

Команда `cheat` есть внутри exe 1.61, но не подключена (`tools/exe_console_commands.py`). Поэтому деньги, уровень и навыки меняются прямо в сохранении. Оба скрипта читают шифрованные и текстовые сохранения. Перед записью они копируют папку сохранения в `Documents\Euro Truck Simulator 2\save_backups\`, а `--restore` возвращает последнюю копию.

```
python tools/save_money.py --save autosave --set 50000000 --apply
python tools/save_profile.py --save autosave                 # опыт, уровень, навыки
python tools/save_profile.py --save autosave --max           # пробный прогон
python tools/save_profile.py --save autosave --max --apply
```

`--max` ставит опыт для уровня 100 (575 700) и все навыки на максимум: ADR 63 (все 6 классов), остальные пять по 6.

## Тесты и пересборка

```
.venv\Scripts\python -m unittest discover -s tests -v
python tools/build_mods.py --install
```

Не для TruckersMP и не для Конвоя.

## Локальные сборки и пакет для Мастерской

- `python tools/build_mods.py --install` собирает локальные `alexey_*.scs` автора (то же содержимое, свои имена пакетов) в `build/` и `Документы\Euro Truck Simulator 2\mod`.
- `python tools/build_workshop.py` собирает публичные версии «OpenRoad»: папки для Мастерской в `workshop/` и файлы выпуска в `release/`. Подробно - в [WORKSHOP.md](WORKSHOP.md).

Обе сборки читают файлы самой игры из установки Steam; файлов SCS в репозитории нет. Если обновление игры переименует параметр, сборка остановится с ошибкой.

## Лицензия

Инструменты и описания правок - под лицензией MIT (файл LICENSE). Изменённые def-файлы внутри `.scs` сделаны из данных Euro Truck Simulator 2 (SCS Software).
