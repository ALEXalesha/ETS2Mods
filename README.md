# EuroTrackMyMods

Personal single-player mods for Euro Truck Simulator 2 (built for game version 1.61.1.1), plus tools: a HashFS reader, save editors for money, level and skills, a console-command checker and a test suite.

| Mod file | In-game name | What it does |
|---|---|---|
| `alexey_hyper_power.scs` | Hyper Power (Alexey) | Extreme version of Super Power: torque x12, final drive x0.35, almost no air drag, more grip, brakes x4. Use instead of Super Power. |
| `alexey_super_power.scs` | Super Power (Alexey) | Torque x3 on every engine, half the air drag, brakes x2. |
| `alexey_money.scs` | Big Money (Alexey) | About 10x job pay; a new profile starts with 10,000,000 EUR. |
| `alexey_free_services.scs` | Free Services (Alexey) | Fuel almost free, ferries and the Channel train free, free towing, emergency refuel/recharge and wear restore. |
| `alexey_no_sleep_fuel.scs` | No Sleep & No Fuel (Alexey) | The driver never gets tired; engines use 1/10000 of the fuel. |
| `alexey_no_fines.scs` | No Fines (Alexey) | No police or camera fines, no cancel fine, no cargo damage pay cut, 30 days for late jobs. |
| `alexey_no_rollover.scs` | No Rollover (Alexey) | Front anti-roll bar 3x stiffer; see the stability sliders below. |
| `alexey_no_damage.scs` | No Damage (Alexey) | No collision damage, no wear, no cargo damage. |
| `alexey_more_traffic.scs` | More Traffic (Alexey) | AI vehicle limit 300; density is `g_traffic` in config.cfg. |

The repository contains no original SCS files. `tools/build_mods.py` reads them from the installed game (`def.scs` and the `dlc_*.scs` archives), changes only the listed values and packs the mods. If a game update renames a parameter, the build stops with an error.

## Load order

The game's own Mod Manager hint: "Mods are prioritized from top to bottom in the Active Mods window - the first mod listed ... has the highest priority."

Top to bottom (`mods/order.json`):

1. Hyper Power (or leave it off and use Super Power)
2. Super Power (turn it off when Hyper Power is on; below Hyper Power it is fully covered and does nothing)
3. Big Money
4. Free Services
5. No Sleep & No Fuel
6. No Fines
7. No Rollover
8. No Damage
9. More Traffic
10. Workshop and other mods

Some of our mods share a file: `def/economy_data.sii` (Big Money, Free Services, No Sleep & No Fuel, No Fines), the 203 engine files (Super Power, No Sleep & No Fuel) and `def/vehicle/physics.sii` (Super Power, No Rollover). The copy in each mod also carries the changes of every mod below it in this order, so nothing is lost. Hyper Power is the exception: it replaces Super Power ("replaces" in order.json), so it carries No Sleep & No Fuel and No Rollover but not Super Power's x3. The flip side: a mod used alone also brings those lower changes with it. For example, Super Power alone also gives near-zero fuel use and the stiffer anti-roll bar.

Workshop mods that replace the same files:

| Workshop mod | File | Note |
|---|---|---|
| Speeding ticket removal (1248269969) | def/police_data.sii | Only removes speeding fines. Keep No Fines above it or turn it off. |
| No Damage by rasmusolle (1724816341) | def/damage_data.sii | Same as our No Damage. Keep one. |
| Brutal Traffic (3103116974), Real Traffic Density (1236032431) | def/traffic_data.sii | Only one traffic_data wins. |
| ETS2 Ultra Realistic Truck Physics (3617215611) | def/vehicle/physics.sii | Super Power and No Rollover above it replace its physics values. |

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

### No Sleep & No Fuel

| File | Parameter | Stock | Mod |
|---|---|---|---|
| def/economy_data.sii | maximum_driving_time (u32, minutes) | 660 | 10000000 |
| def/vehicle/truck/*/engine/*.sii (203 engines, 26 truck models) | consumption_coef (float) | not set | 0.0001 (new line) |

`consumption_coef` is not used in any stock file. The exe's attribute table lists it for `accessory_engine_data` as a float (type 0x05, like `torque`). It is 0.0001 rather than 0, for the same divide-by-zero reason as the fuel price (dashboard average/range). The cleanest way to turn off sleep without a mod is the game option "Fatigue simulation" (`g_fatigue`, currently 1 in the profile).

### Super Power

| File | Parameter | Stock | Mod |
|---|---|---|---|
| def/vehicle/truck/*/engine/*.sii (203 engines) | torque | 1300 to 3800 Nm | x3 (3900 to 11400) |
| same | secondary_torque (where present) | per engine | x3 |
| def/vehicle/physics.sii | air_resistance | 3.0 | 1.5 |
| def/vehicle/physics.sii | brake_torque_factor | 1.0 | 2.0 |

Covered trucks: DAF XF, XF Euro 6, XF Electric, 2021, XD; Iveco Stralis, Hi-Way, S-Way; MAN TGX, TGX Euro 6, TGX 2020; Mercedes Actros, Actros 2014; Renault Magnum, Premium, T, E-Tech T; Scania R, R 2016, S 2016, S 2024E, Streamline; Volvo FH16, FH16 2012, FH 2021, FH 2024. Not covered: trucks from other mods or DLCs not installed, and AI traffic.

What caps the speed:
- The speed limiter. This is the game option "Speed limiter" (`g_use_speed_limiter`), already 0 in the profile. `game_data` also has `truck_speed_limit` (u32) for when the limiter is on.
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

The real lever is in the game options, Gameplay: "Vehicle stability" (`g_truck_stability`, profile value 0) and "Trailer stability" (`g_trailer_stability`, 0.075). Per the game's tooltip they lower the centre of gravity; set both to maximum. Truck centre of gravity comes from the vehicle models, not from def files, so "never tips over" cannot be guaranteed by a mod.

### Big Money

| File | Parameter | Stock | Mod |
|---|---|---|---|
| def/economy_data.sii | revenue_per_km_base | 15 | 150 |
| def/economy_data.sii | fixed_revenue | 600 | 6000 |
| def/initial_save/normal/game.sii | money_account | 2000 | 10000000 |

### More Traffic and config.cfg

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

## Steam Workshop

`tools/build_workshop.py` builds neutral "OpenRoad" Workshop folders (`workshop/`, not committed) from the same sources. Upload steps are in [WORKSHOP.md](WORKSHOP.md). The local `alexey_*.scs` builds keep their names so existing saves and the active mod list stay valid.
