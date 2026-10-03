# ETS2Mods - OpenRoad mods for Euro Truck Simulator 2

Ten single-player mods for Euro Truck Simulator 2 (game version 1.61), plus the tools that build them from the game's own files: a HashFS reader, save editors for money, level and skills, and a test suite.

> Not affiliated with or endorsed by SCS Software. "Euro Truck Simulator 2" is a trademark of SCS Software. The mods are fan-made and for single player only; they do not work on TruckersMP or in Convoy.

| Mod (release file) | What it does |
|---|---|
| OpenRoad: Hyper Power (`OpenRoad_Hyper_Power.scs`) | Extreme: torque x12, final drive x0.35 (about 460-590 km/h gear-limited), almost no air drag, grip +30%, brakes x4. Use instead of Super Power. |
| OpenRoad: Super Power (`OpenRoad_Super_Power.scs`) | Torque x3, half the air drag, brakes x2. Still drivable. |
| OpenRoad: Big Money (`OpenRoad_Big_Money.scs`) | About 10x job pay; a new profile starts with 10,000,000 EUR. |
| OpenRoad: Free Services (`OpenRoad_Free_Services.scs`) | Fuel almost free (0.0001 EUR/l), ferries and the Channel train free, free towing, emergency refuel/recharge and wear restore. |
| OpenRoad: No Sleep (`OpenRoad_No_Sleep.scs`) | The driver never gets tired. |
| OpenRoad: No Fuel (`OpenRoad_No_Fuel.scs`) | Engines use 1/10000 of the fuel. |
| OpenRoad: No Fines (`OpenRoad_No_Fines.scs`) | No police or camera fines, no cancel fine, no cargo damage pay cut, 30 days for late jobs. |
| OpenRoad: No Rollover (`OpenRoad_No_Rollover.scs`) | Front anti-roll bar 3x stiffer; plus the game's stability sliders. |
| OpenRoad: No Damage (`OpenRoad_No_Damage.scs`) | No collision damage, no wear, no cargo damage. |
| OpenRoad: More Traffic (`OpenRoad_More_Traffic.scs`) | AI vehicle limit 300; density via the game variable `g_traffic`. |

## Install

- **Steam Workshop:** subscribe to the OpenRoad items, then turn them on in the in-game Mod Manager.
- **From the releases:** download the `.scs` files from the [latest release](../../releases/latest) and put them into `Documents\Euro Truck Simulator 2\mod`. Then turn them on in the Mod Manager (profile -> Mod Manager), in the order below.

## Load order

The game's own Mod Manager hint: "Mods are prioritized from top to bottom in the Active Mods window - the first mod listed ... has the highest priority."

Top to bottom (`mods/order.json`):

1. Hyper Power (or leave it off and use Super Power)
2. Super Power (turn it off when Hyper Power is on; below Hyper Power it is fully covered and does nothing)
3. Big Money
4. Free Services
5. No Sleep
6. No Fuel
7. No Fines
8. No Rollover
9. No Damage
10. More Traffic
11. other mods

Some mods share a file: `def/economy_data.sii` (Big Money, Free Services, No Sleep, No Fines), the 203 engine files (Hyper/Super Power, No Fuel) and `def/vehicle/physics.sii` (Hyper/Super Power, No Rollover). The game uses only the top-most copy, so each mod also carries the changes of every mod below it in this order, and nothing is lost. Hyper Power replaces Super Power, so it does not carry Super Power's x3. The flip side: a mod used alone also brings the lower mods' changes for the shared files. For example, Big Money alone also gives free towing.

Other mods that replace the same files (`police_data.sii`, `damage_data.sii`, `traffic_data.sii`, `physics.sii`, engine or transmission files) override, or are overridden by, these mods depending on the order.

## Changed values

### No Fines

| File | Parameter | Stock | Mod |
|---|---|---|---|
| def/police_data.sii | fine_factor_base / fine_factor_step | 0.2 / 0.08 | 0 / 0 |
| def/police_data.sii | fine_amounts[0..13] | 100 to 2000 | 0 |
| def/police_data.sii | offence_probabilty[0..13] | 0.0 to 1.0 | 0.0 |
| def/police_data.sii | offence_police_probabilty[0..13] | 0.3 to 1.0 | 0.0 |
| def/economy_data.sii | abandoned_job_fine | 12000 | 0 |
| def/economy_data.sii | cargo_damage_cost / cargo_damage_cost_factor | 5.0 / 0.04 | 0 / 0 |
| def/economy_data.sii | late_delivery_max_overtime[0..2] | 2880 / 720 / 240 min | 43200 min |

### No Damage

| File | Parameter | Stock | Mod |
|---|---|---|---|
| def/damage_data.sii | truck_damage_coef / trailer_damage_coef | 0.0007 / 0.0007 | 0 / 0 |
| def/damage_data.sii | dragged_trailer_damage_coef | 0.00002 | 0 |
| def/damage_data.sii | truck_to_trailer_dmg | 0.2 | 0 |
| def/damage_data.sii | cargo_damage_ratio | 1.0 | 0 |
| def/damage_data.sii | engine_wear / transmission_wear / wheel_wear | 2e-6 | 0 |
| def/damage_data.sii | engine_wear_unfixable / transmission_wear_unfixable | 2e-7 | 0 |
| def/damage_data.sii | wheel_wear_unfixable | 2e-5 | 0 |
| def/damage_data.sii | trailer_wheel_wear / trailer_wheel_wear_unfixable | 2e-6 / 2e-5 | 0 / 0 |

### Free Services

| File | Parameter | Stock | Mod |
|---|---|---|---|
| def/economy_data.sii | tow_price_base / tow_price_factor | 150 / 0.4 | 0 / 0 |
| def/economy_data.sii | refuel_price_base / refuel_price_factor | 150 / 3 | 0 / 0 |
| def/economy_data.sii | recharge_price_base / recharge_price | 150 / 2 | 0 / 0 |
| def/service_data.sii | truck_restore_accessory_fixed_price / _price_coef | 1000 / 1.1 | 0 / 0 |
| def/service_data.sii | trailer_restore_accessory_fixed_price / _price_coef | 1000 / 1.1 | 0 / 0 |
| def/country/*.sui (36 countries) | fuel_price | 0.829 to 2.555 | 0.0001 |
| def/ferry/connection/*.sii (19 crossings incl. the Channel train) | price | 65 to 1212 | 0 |

Why fuel_price is 0.0001 and not 0: with 0 the refuel panel showed "Litres: -nan(ind)". The panel in `eurotrucks2.exe` (the `gas_station_hud` format `@@diesel_price@@: %s<br>%s: %.2f<br>@@total_price@@: %s`) computes litres as `total_cost / fuel_price` (`divss` at 0xA5B30D, then times 1.0, 0.264172 or 0.219969 for litres, US or imperial gallons). There is no zero check, so 0/0 gives NaN. The total is shown as `floor(cost + 0.5)` in whole currency units. At 0.0001 EUR/l, a 1000 l fill costs 0.10 EUR, which displays as 0. The price line shows the smallest non-zero amount (about RUB 0.01). `tests/test_mods.py` fails if any built fuel_price is exactly 0.

### No Sleep and No Fuel

Two separate mods since 1.1.0 (one combined mod before).

| Mod | File | Parameter | Stock | Mod |
|---|---|---|---|---|
| No Sleep | def/economy_data.sii | maximum_driving_time (u32, minutes) | 660 | 10000000 |
| No Fuel | def/vehicle/truck/*/engine/*.sii (203 engines, 26 truck models) | consumption_coef (float) | not set | 0.0001 (new line) |

`consumption_coef` is not used in any stock file. The exe's attribute table lists it for `accessory_engine_data` as a float (type 0x05, like `torque`). It is 0.0001 rather than 0, for the same divide-by-zero reason as the fuel price (dashboard average/range). The cleanest way to turn off sleep without a mod is the game option "Fatigue simulation" (`g_fatigue`).

### Super Power

| File | Parameter | Stock | Mod |
|---|---|---|---|
| def/vehicle/truck/*/engine/*.sii (203 engines) | torque | 1300 to 3800 Nm | x3 (3900 to 11400) |
| same | secondary_torque (where present) | per engine | x3 |
| def/vehicle/physics.sii | air_resistance | 3.0 | 1.5 |
| def/vehicle/physics.sii | brake_torque_factor | 1.0 | 2.0 |

Covered trucks: DAF XF, XF Euro 6, XF Electric, 2021, XD; Iveco Stralis, Hi-Way, S-Way; MAN TGX, TGX Euro 6, TGX 2020; Mercedes Actros, Actros 2014; Renault Magnum, Premium, T, E-Tech T; Scania R, R 2016, S 2016, S 2024E, Streamline; Volvo FH16, FH16 2012, FH 2021, FH 2024. Not covered: trucks from other mods or DLCs not installed, and AI traffic.

What caps the speed:
- The speed limiter. This is the game option "Speed limiter" (`g_use_speed_limiter`). `game_data` also has `truck_speed_limit` (u32) for when the limiter is on.
- Air drag. physics.sii says `resistant_force = air_resistance * speed^2`; halving it raises the drag-limited speed by about 26%, and x3 power adds about 44% more.
- Gearing and rpm. Torque curves end at about 2500 rpm (e.g. Scania DC13: 0.1 of torque at 2500). With a 0.8 overdrive, a typical 2.6 axle ratio and about 0.5 m tyre radius, that is roughly 200 to 225 km/h. "Infinite" speed is not reachable without editing gearboxes and torque curves.
- `physics_data` also has a float `user_engine_boost` in the exe, but its effect cannot be checked from the files, so it is not used.

### Hyper Power

| File | Parameter | Stock | Mod |
|---|---|---|---|
| def/vehicle/truck/*/engine/*.sii (203 engines) | torque, secondary_torque | 1300 to 3800 Nm | x12 (15600 to 45600) |
| def/vehicle/truck/*/transmission/*.sii (170 gearboxes, 26 trucks) | differential_ratio | 2.38 to 4.83 | x0.35 |
| def/vehicle/physics.sii | air_resistance | 3.0 | 0.1 (not 0) |
| def/vehicle/physics.sii | brake_torque_factor | 1.0 | 4.0 |
| def/vehicle/physics.sii | brake_cooling_rate | 0.01 | 0.05 |
| def/vehicle/physics.sii | steering_sensitivity_multiplier_minimum | 0.2 | 0.1 |
| def/vehicle/f_tire, r_tire (31 tyres) | grip_factor (float, code default 1.0) | not set | 1.3 (new line) |

Top speed from the real numbers (`python tools/top_speed.py`). Formula: v = rpm/60 x 2*pi*0.506 m / (top gear x final drive), where 0.506 m is the radius of a 315/70 R22.5 tyre and rpm is where the torque curve ends (median 2200).

| | Top-gear overall ratio (best / median) | Gear-limited top speed |
|---|---|---|
| Stock | 2.020 / 2.620 | 208 / 160 km/h |
| Hyper Power | 0.707 / 0.917 | about 590 / 460 km/h |

At 460 km/h the air drag with a=0.1 needs about 0.2 MW. A x12 engine gives several MW near the end of its curve, so gearing and rpm set the cap, not power (rolling resistance is left out of this estimate). The DAF XF Electric single-speed box (ratio 2.71 after the mod) depends on the motor's 8000 rpm curve.

What still caps it:
- the end of the torque curve. Rpm and curves were not stretched: automatic shift points (`rpm_range_*`), the tachometers and the engine sounds are tied to them;
- the physics step: at 130+ m/s a truck moves more than 2 m per physics frame, so thin collisions can be missed;
- map streaming, which may lag behind;
- the cab speedometer needle stops at its end mark; the HUD/navigation number keeps counting.

No speed hard cap was found in the exe strings. AI traffic does not react to your speed. Speed cameras fine you only without No Fines.

Low-gear launch: wheel torque is about 4.2x stock (12 x 0.35), so traction control (`g_anti_slip`, on) may cut power on an empty truck. Grip +30% helps. More grip also raises rollover risk in fast corners: keep No Rollover and the stability sliders at max.

### No Rollover

| File | Parameter | Stock | Mod |
|---|---|---|---|
| def/vehicle/physics.sii | sway_bar_stiffness_factor (front axle anti-roll bar) | 1.0 | 3.0 |

The real lever is in the game options, Gameplay: "Vehicle stability" (`g_truck_stability`, stock 0) and "Trailer stability" (`g_trailer_stability`). Per the game's tooltip they lower the centre of gravity; set both to maximum. Truck centre of gravity comes from the vehicle models, not from def files, so "never tips over" cannot be guaranteed by a mod.

### Big Money

| File | Parameter | Stock | Mod |
|---|---|---|---|
| def/economy_data.sii | revenue_per_km_base | 15 | 150 |
| def/economy_data.sii | fixed_revenue | 600 | 6000 |
| def/initial_save/normal/game.sii | money_account | 2000 | 10000000 |

### More Traffic and config.cfg (author's setup)

| File | Parameter | Stock | Now |
|---|---|---|---|
| def/traffic_data.sii | max_vehicle_count | not set (commented 50) | 300 |
| config.cfg | g_traffic / g_developer / g_console / g_save_format | 1.0 / 0 / 0 / 0 | 3.0 / 1 / 1 / 2 (text saves) |

## Not changed, and why

- Road tolls: the amounts are in the map data. The economy fields `toll_fees`, `truck_scales_cost` and `oversize_job_cancel_cost` exist in the exe with unusual types (0x00, 0x02, 0x07), so they are left alone.
- Repair of existing damage: computed in code from part prices.
- Quick travel: no cost parameter in def files.

## Save editors (game closed)

The console command `cheat` is compiled into 1.61 but never registered (`tools/exe_console_commands.py`), so money, level and skills are changed in the save. Both tools read encrypted binary saves (ScsC + BSII) and text saves. Before writing they copy the save folder to `Documents\Euro Truck Simulator 2\save_backups\`, and `--restore` puts the latest backup back.

```
python tools/save_money.py                                        # list saves and money
python tools/save_money.py --save autosave --set 50000000 --apply
python tools/save_profile.py --save autosave                      # XP, level, skills
python tools/save_profile.py --save autosave --max                # dry run
python tools/save_profile.py --save autosave --max --apply
```

`save_profile.py --max` sets `experience_points` to the XP for level 100 (575,700) and sets all skills to maximum: `adr` 63 (bit mask of the six ADR classes), and `long_dist`, `heavy` (high value), `fragile`, `urgent` (just-in-time), `mechanical` (ecodriving) to 6. The level thresholds are read from `def/economy_data_xp.sii`.

## Tests

```
.venv\Scripts\python -m unittest discover -s tests -v
```

The suite builds all mods into a temp folder and checks:
- no fuel_price or consumption_coef is 0;
- manifests, the 276x162 icons and no zip directory entries;
- every patch landed and shared files carry the lower mods' changes;
- all 203 engines are covered with torque x3;
- known CityHash values;
- the save parsers, on synthetic and real saves.

## Rebuild after a game update

```
python tools/build_mods.py --install
```

To change a value, edit `mods/<name>/mod.json` (operations are described at the top of `tools/build_mods.py`). The order is in `mods/order.json`. Icons: `.venv\Scripts\python tools\make_icons.py`. Packages: `tools/requirements.txt`.

## Tools

- `tools/hashfs.py`: HashFS v1/v2 reader. Paths are hashed with CityHash64 1.0.x (`tools/cityhash103.py`); the PyPI `cityhash` package is 1.1 and gives different hashes.
- `tools/sii_save.py`: ScsC decryption and a BSII reader.
- `tools/save_money.py`, `tools/save_profile.py`: save editors.
- `tools/exe_console_commands.py`: console command registration check.
- `tools/build_mods.py`, `tools/make_icons.py`: build.

Not for TruckersMP or Convoy. These are single-player mods.

## Local builds and the Workshop pack

- `python tools/build_mods.py --install` builds the author's local `alexey_*.scs` (same content, own package names) into `build/` and `Documents\Euro Truck Simulator 2\mod`.
- `python tools/build_workshop.py` builds the public "OpenRoad" versions: Workshop folders in `workshop/` and the release files in `release/`. See [WORKSHOP.md](WORKSHOP.md).

Both read the game's own files from the Steam install; no SCS files are stored in this repository. The build stops with an error if a game update renames a parameter.

## License

The tools and patch definitions are under the MIT License (see LICENSE). The changed def files inside the `.scs` packages are derived from Euro Truck Simulator 2 data by SCS Software.
