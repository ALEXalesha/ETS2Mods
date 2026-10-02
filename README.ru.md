# EuroTrackMyMods

Личные моды для одиночной игры Euro Truck Simulator 2 (под версию 1.61.1.1) и инструменты: распаковщик HashFS, правка денег, уровня и навыков в сохранении, проверка консольных команд и тесты.

| Файл | Название в игре | Что делает |
|---|---|---|
| `alexey_hyper_power.scs` | Hyper Power (Alexey) | Безумная версия Super Power: момент x12, главная пара x0.35, почти без сопротивления воздуха, сцепление +30%, тормоза x4. Вместо Super Power. |
| `alexey_super_power.scs` | Super Power (Alexey) | Крутящий момент всех двигателей x3, сопротивление воздуха вдвое меньше, тормоза x2. |
| `alexey_money.scs` | Big Money (Alexey) | Оплата рейсов примерно x10, новый профиль начинает с 10 000 000 €. |
| `alexey_free_services.scs` | Free Services (Alexey) | Топливо почти даром, паромы и поезд бесплатно, бесплатные эвакуация, экстренная заправка и зарядка, восстановление износа. |
| `alexey_no_sleep_fuel.scs` | No Sleep & No Fuel (Alexey) | Водитель не устаёт, двигатели тратят 1/10000 топлива. |
| `alexey_no_fines.scs` | No Fines (Alexey) | Нет штрафов полиции и камер, нет штрафа за отказ, повреждение груза не уменьшает оплату, 30 дней на опоздание. |
| `alexey_no_rollover.scs` | No Rollover (Alexey) | Передний стабилизатор в 3 раза жёстче; плюс ползунки устойчивости в настройках. |
| `alexey_no_damage.scs` | No Damage (Alexey) | Нет урона, износа и повреждения груза. |
| `alexey_more_traffic.scs` | More Traffic (Alexey) | Лимит машин ИИ 300; плотность задаёт `g_traffic` в config.cfg. |

Оригинальных файлов SCS в репозитории нет. `tools/build_mods.py` берёт их из установленной игры (`def.scs` и архивы `dlc_*.scs`), меняет только нужные значения и собирает моды. Если обновление переименует параметр, сборка остановится с ошибкой.

## Порядок модов

Подсказка самой игры: «Приоритет модов определяется их положением в списке активных модов». Верхний - главный.

Сверху вниз (`mods/order.json`):

1. Hyper Power (или выключен, если нужен Super Power)
2. Super Power (при включённом Hyper Power выключить; ниже Hyper Power он всё равно ничего не делает)
3. Big Money
4. Free Services
5. No Sleep & No Fuel
6. No Fines
7. No Rollover
8. No Damage
9. More Traffic
10. моды Мастерской и прочие

Некоторые наши моды меняют один и тот же файл:
- `economy_data.sii` - Big Money, Free Services, No Sleep & No Fuel, No Fines;
- 203 файла двигателей - Super Power, No Sleep & No Fuel;
- `physics.sii` - Super Power, No Rollover.

Копия файла в каждом моде несёт и правки всех модов ниже по списку, поэтому при таком порядке ничего не теряется. Обратная сторона: мод в одиночку тоже приносит правки нижних. Например, Super Power в одиночку тоже даёт почти нулевой расход и жёсткий стабилизатор.

Моды Мастерской с теми же файлами:

| Мод | Файл | Что делать |
|---|---|---|
| Speeding ticket removal (1248269969) | police_data.sii | Держать ниже No Fines или выключить. |
| No Damage от rasmusolle (1724816341) | damage_data.sii | То же, что наш No Damage. Оставить один. |
| Brutal Traffic, Real Traffic Density | traffic_data.sii | Работает только один. |
| ETS2 Ultra Realistic Truck Physics (3617215611) | physics.sii | Наши Super Power и No Rollover выше него заменят его физику. |

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

### No Sleep & No Fuel
| Файл | Параметр | Было | Стало |
|---|---|---|---|
| economy_data.sii | maximum_driving_time (мин) | 660 | 10000000 |
| truck/*/engine/*.sii (203 двигателя, 26 моделей) | consumption_coef | нет | 0.0001 (новая строка) |

`consumption_coef` в файлах игры не встречается. По таблице атрибутов в exe это float у `accessory_engine_data`, как `torque`. Ровно 0 не ставится по той же причине деления на ноль (средний расход и запас хода). Самый простой способ отключить сон без мода - снять галочку «Эмуляция усталости» в настройках (`g_fatigue`, сейчас 1).

### Super Power
| Файл | Параметр | Было | Стало |
|---|---|---|---|
| truck/*/engine/*.sii (203 двигателя) | torque | 1300-3800 Нм | x3 (3900-11400) |
| то же | secondary_torque (где есть) | разный | x3 |
| vehicle/physics.sii | air_resistance | 3.0 | 1.5 |
| vehicle/physics.sii | brake_torque_factor | 1.0 | 2.0 |

Охвачены все 26 моделей игры и установленных DLC (DAF, Iveco, MAN, Mercedes, Renault, Scania, Volvo). Не охвачены грузовики из других модов и неустановленных DLC.

Что ограничивает скорость:
- Ограничитель скорости - это галочка в настройках (`g_use_speed_limiter`, у Алексея уже 0).
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

Hyper Power заменяет Super Power: правки No Sleep & No Fuel и No Rollover он несёт, а x3 от Super Power - нет.

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

Главное средство - в настройках, раздел «Геймплей»: «Устойчивость транспортного средства» (`g_truck_stability`, сейчас 0) и «Устойчивость прицепа» (`g_trailer_stability`, 0.075). По подсказке игры они опускают центр тяжести; поставить оба на максимум. Центр тяжести грузовика задают модели, а не def-файлы, поэтому «никогда не переворачивается» мод гарантировать не может.

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
