# ETS2Mods

Three personal single-player mods for Euro Truck Simulator 2 (built for game version 1.61.1.1), plus a small reader for SCS HashFS archives.

| Mod file | In-game name | What it does |
|---|---|---|
| `alexey_no_fines.scs` | No Fines (Alexey) | All police and camera fines are 0 and offences are not registered. No fine for abandoning a job, no pay cut for cargo damage, and late jobs stay valid for 30 days. |
| `alexey_more_traffic.scs` | More Traffic (Alexey) | Raises the total AI vehicle limit to 300. The density itself is set by `g_traffic` in `config.cfg`. |
| `alexey_money.scs` | Big Money (Alexey) | About 10x job pay. A new profile starts with 10,000,000 EUR. Also includes the economy part of No Fines. |

The repository contains no original SCS files. `tools/build_mods.py` reads them from your installed game, changes only the listed values and packs the mods. If a game update renames a parameter, the build stops with an error instead of producing a broken mod.

## Changed values

| File | Parameter | Stock | Mod |
|---|---|---|---|
| def/police_data.sii | fine_factor_base | 0.2 | 0.0 |
| def/police_data.sii | fine_factor_step | 0.08 | 0.0 |
| def/police_data.sii | fine_amounts[0..13] | 100 to 2000 | 0 |
| def/police_data.sii | offence_probabilty[0..13] | 0.0 to 1.0 | 0.0 |
| def/police_data.sii | offence_police_probabilty[0..13] | 0.3 to 1.0 | 0.0 |
| def/economy_data.sii | abandoned_job_fine | 12000 | 0 |
| def/economy_data.sii | cargo_damage_cost | 5.0 | 0.0 |
| def/economy_data.sii | cargo_damage_cost_factor | 0.04 | 0.0 |
| def/economy_data.sii | late_delivery_max_overtime[0..2] | 2880 / 720 / 240 min | 43200 min (30 days) |
| def/economy_data.sii | revenue_per_km_base | 15 | 150 (Big Money only) |
| def/economy_data.sii | fixed_revenue | 600 | 6000 (Big Money only) |
| def/initial_save/normal/game.sii | money_account | 2000 | 10000000 (Big Money only) |
| def/traffic_data.sii | max_vehicle_count | not set (commented default 50) | 300 |
| config.cfg (user folder) | g_traffic | 1.0 | 3.0 |
| config.cfg (user folder) | g_developer / g_console | 0 / 0 | 1 / 1 |

All of these names come from the game's own files. The console command and the `g_traffic` range (0 to 10) were checked in the strings of `eurotrucks2.exe`.

## Load order

In the Mod Manager, mods higher in the active list win. Both No Fines and Big Money replace `def/economy_data.sii`, so put **Big Money above No Fines**. Big Money already contains the No Fines economy changes, so you lose nothing that way. Put all three above any Workshop mod that touches the same files, for example traffic density or ticket removal mods.

## Traffic density

`g_traffic` is the multiplier. Stock is 1.0 and the game accepts 0.0 to 10.0. 3.0 is a safe start; 4 to 5 is a lot in big cities and costs FPS. You can change it in the console during play (`g_traffic 4`), or in `config.cfg` while the game is closed.

## Money from the console

`config.cfg` now has `g_developer "1"` and `g_console "1"`. A backup of the original is next to it: `config.cfg.2026-10-02.bak`. In game, open the console with the `~` key (the key below Esc) and type:

```
cheat money 1000000
```

The exe usage string is `cheat money [amount] [set]`.

## Rebuild after a game update

```
python tools/build_mods.py --install
```

This reads the new `def.scs`, sets `compatible_versions` from `version.scs` and copies the mods to `Documents\Euro Truck Simulator 2\mod`. To change a value, edit `mods/<name>/mod.json`. To redraw the icons, run `.venv\Scripts\python tools\make_icons.py` (needs Pillow: `pip install -r tools/requirements.txt` in the venv).

## HashFS reader

`tools/hashfs.py` reads HashFS v1 and v2 archives using only the standard library:

```
python tools/hashfs.py ls      <archive.scs> def
python tools/hashfs.py tree    <archive.scs> def/country
python tools/hashfs.py cat     <archive.scs> def/economy_data.sii
python tools/hashfs.py extract <archive.scs> extracted def/police_data.sii def/initial_save
```

Notes from building it:
- Paths are hashed with **CityHash64 version 1.0.x**. The `cityhash` package on PyPI implements 1.1 and gives different hashes. It only matches for the empty root path, which is misleading. `tools/cityhash103.py` is a pure Python 1.0.x port.
- v2 header: `SCS#`, u16 version, u16 salt, `CITY`, entry count, compressed entry table size, metadata count, compressed metadata table size, entry table offset, metadata table offset. Both tables are zlib-compressed.
- An entry is 16 bytes: hash u64, metadata index u32, metadata count u16, flags u16 (bit 0 = directory). A metadata word has its type in the high byte (0x80 plain, 0x81 directory, 0x01 image) and its index in the low 24 bits. Plain data: compressed size (low 28 bits) with compression in the top 4 bits (1 = zlib), size, unused, offset in 16-byte blocks.
- A v2 directory listing: u32 count, count length bytes, then names. Subdirectories start with `/`.
- In 1.61 the def files are plain text, not encrypted or binary SII.

Not for TruckersMP or Convoy. These are single-player mods.
