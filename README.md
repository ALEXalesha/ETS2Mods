# EuroTrackMyMods

Personal single-player mods for Euro Truck Simulator 2 (built for game version 1.61.1.1), plus small tools: a HashFS reader, a save-money editor and a console-command checker.

| Mod file | In-game name | What it does |
|---|---|---|
| `alexey_money.scs` | Big Money (Alexey) | About 10x job pay. A new profile starts with 10,000,000 EUR. Also contains the economy parts of Free Services and No Fines. |
| `alexey_free_services.scs` | Free Services (Alexey) | Free fuel, free ferries and the Channel train, free emergency call / towing, free emergency refuel and recharge, free wear restore. Also contains the economy part of No Fines. |
| `alexey_no_fines.scs` | No Fines (Alexey) | All police and camera fines are 0 and offences are not registered. No fine for abandoning a job, no pay cut for cargo damage, late jobs stay valid for 30 days. |
| `alexey_no_damage.scs` | No Damage (Alexey) | No collision damage to truck and trailer, no wear, no cargo damage. |
| `alexey_more_traffic.scs` | More Traffic (Alexey) | Raises the total AI vehicle limit to 300. Density itself is `g_traffic` in `config.cfg`. |

The repository contains no original SCS files. `tools/build_mods.py` reads them from the installed game, changes only the listed values and packs the mods. If a game update renames a parameter, the build stops with an error.

## Load order

The game's own hint (Mod Manager): "Mods are prioritized from top to bottom in the Active Mods window - the first mod listed ... has the highest priority."

Recommended order, top to bottom:

1. Big Money (Alexey)
2. Free Services (Alexey)
3. No Fines (Alexey)
4. No Damage (Alexey)
5. More Traffic (Alexey)
6. everything else

Big Money, Free Services and No Fines all replace `def/economy_data.sii`. Each one higher in this list already carries the economy changes of the ones below it, so with this order nothing is lost. The flip side: Big Money alone also gives free towing and no cancel fine.

Workshop mods that replace the same files (checked in the Workshop folder):

| Workshop mod | File | Note |
|---|---|---|
| Speeding ticket removal (1248269969) | def/police_data.sii | Only removes speeding fines. Keep No Fines above it or turn it off. |
| No Damage by rasmusolle (1724816341) | def/damage_data.sii | Same purpose as our No Damage. Keep one. |
| Brutal Traffic (3103116974) | def/traffic_data.sii | Sets max_vehicle_count 4500 and AI behaviour. Only one traffic_data wins. |
| Real Traffic Density (1236032431) | def/traffic_data.sii | Sets max_vehicle_count 500 and spawn distances. |

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
| def/damage_data.sii | truck_damage_coef | 0.0007 | 0 |
| def/damage_data.sii | trailer_damage_coef | 0.0007 | 0 |
| def/damage_data.sii | dragged_trailer_damage_coef | 0.00002 | 0 |
| def/damage_data.sii | truck_to_trailer_dmg | 0.2 | 0 |
| def/damage_data.sii | cargo_damage_ratio | 1.0 | 0 |
| def/damage_data.sii | engine_wear / transmission_wear / wheel_wear | 2e-6 each | 0 |
| def/damage_data.sii | engine_wear_unfixable / transmission_wear_unfixable | 2e-7 each | 0 |
| def/damage_data.sii | wheel_wear_unfixable | 2e-5 | 0 |
| def/damage_data.sii | trailer_wheel_wear / trailer_wheel_wear_unfixable | 2e-6 / 2e-5 | 0 |

cabin, chassis and trailer body/chassis wear are already 0 in the stock file.

### Free Services

| File | Parameter | Stock | Mod |
|---|---|---|---|
| def/economy_data.sii | tow_price_base / tow_price_factor | 150 / 0.4 | 0 / 0 |
| def/economy_data.sii | refuel_price_base / refuel_price_factor | 150 / 3 | 0 / 0 |
| def/economy_data.sii | recharge_price_base / recharge_price | 150 / 2 | 0 / 0 |
| def/service_data.sii | truck_restore_accessory_fixed_price / _price_coef | 1000 / 1.1 | 0 / 0 |
| def/service_data.sii | trailer_restore_accessory_fixed_price / _price_coef | 1000 / 1.1 | 0 / 0 |
| def/country/*.sui (36 countries) | fuel_price | 0.829 to 2.555 | 0 |
| def/ferry/connection/*.sii (19 crossings, incl. the Channel tunnel train) | price | 65 to 1212 | 0 |

`truck_restore_fixed_price` and `trailer_restore_fixed_price` are already 0 in the stock file.

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
| config.cfg | g_traffic | 1.0 | 3.0 (game accepts 0 to 10) |
| config.cfg | g_developer / g_console | 0 / 0 | 1 / 1 |
| config.cfg | g_save_format | 0 | 2 (text saves) |

## Not changed, and why

- Road tolls. Toll gates and their amounts are in the map data, not in def files. The exe also knows an economy field `toll_fees`, but its type and meaning cannot be checked from the game files, so it is left alone. The same goes for `truck_scales_cost` and `oversize_job_cancel_cost`.
- Repair of damage you already have. The cost comes from the part prices in code. With No Damage there is nothing new to repair.
- Quick travel / relocation. No separate cost parameter exists in the def files. Emergency call towing is covered by `tow_price_*`.

## Money: the console command does not exist in 1.61

`cheat money 1000000` answers `unknown command` even with `g_developer 1` and `g_console 1`. `tools/exe_console_commands.py` lists the 83 command descriptors compiled into `eurotrucks2.exe`. 79 of them are registered by code. The 4 that are never registered are `cheat` and three profiler commands. So no cvar or launch option can enable `cheat` in this build.

What works instead:

1. Big Money: about 10x pay for every job.
2. `tools/save_money.py` edits the money in a save. Close the game first.

```
python tools/save_money.py                                       # list saves and money
python tools/save_money.py --save autosave --set 50000000        # dry run
python tools/save_money.py --save autosave --set 50000000 --apply
python tools/save_money.py --save autosave --restore             # undo from the backup
```

It reads the default encrypted binary saves (ScsC + BSII) and text saves. Before writing, it copies the save folder to `Documents\Euro Truck Simulator 2\save_backups\`. A binary save is written back as plain BSII without the encryption layer. A text save is edited in place. `g_save_format "2"` is set in `config.cfg`, so new saves will be text.

## Rebuild after a game update

```
python tools/build_mods.py --install
```

To change a value, edit `mods/<name>/mod.json`. A key may use `*` in the file name, for example `def/country/*.sui`. Icons: `.venv\Scripts\python tools\make_icons.py`. Python packages for the tools are in `tools/requirements.txt`; install them in the venv.

## Tools

- `tools/hashfs.py`: reader for HashFS v1/v2 `.scs` archives. Paths are hashed with CityHash64 version 1.0.x (`tools/cityhash103.py`); the PyPI `cityhash` package is version 1.1 and gives different hashes. Commands: `ls`, `tree`, `cat`, `extract`.
- `tools/sii_save.py`: ScsC decryption and a BSII reader. It walks every block and must end exactly at the end marker.
- `tools/save_money.py`: money editor (above).
- `tools/exe_console_commands.py`: console command registration check.
- `tools/build_mods.py`, `tools/make_icons.py`: build.

Not for TruckersMP or Convoy. These are single-player mods.
