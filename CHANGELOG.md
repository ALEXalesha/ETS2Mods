# Changelog

## 1.1.0 - 2026-10-03

- "No Sleep & No Fuel" is now two separate mods: **OpenRoad: No Sleep** (maximum_driving_time 10,000,000 min) and **OpenRoad: No Fuel** (consumption_coef 0.0001 on all 203 engines). There are 10 mods in total.
- Load order: No Sleep and No Fuel take the old place of the combined mod (below Free Services, above No Fines). The shared-file chain is unchanged: Big Money and Free Services carry No Sleep; Hyper and Super Power carry No Fuel.
- Tests: 10 mods; every changed parameter belongs to exactly one mod; the chain carries both new mods; mutation-checked. The personal-data scan treats only the Gitea host as private: the repository names are public.

## 1.0.0 - 2026-10-03

First public release, for Euro Truck Simulator 2 version 1.61.

Mods (public names "OpenRoad: ..."):
- **Hyper Power**: torque x12, final drive x0.35, air resistance 0.1, tyre grip 1.3, brakes x4 (gear-limited top speed about 460-590 km/h). Replaces Super Power.
- **Super Power**: torque x3, air resistance 1.5, brakes x2.
- **Big Money**: job pay about 10x; a new profile starts with 10,000,000 EUR.
- **Free Services**: fuel 0.0001 EUR/l in all 36 countries, all 19 ferries and trains free, free towing, emergency refuel/recharge and wear restore.
- **No Sleep & No Fuel**: maximum_driving_time 10,000,000 min; consumption_coef 0.0001 on all 203 engines.
- **No Fines**: all 14 fines 0 and offences not registered; no cancel fine; no cargo damage pay cut; 30 days for late jobs.
- **No Rollover**: front anti-roll bar 3x stiffer.
- **No Damage**: no collision damage, no wear, no cargo damage.
- **More Traffic**: AI vehicle limit 300.

Fixed during testing:
- With fuel_price 0, the refuel panel showed "Litres: -nan(ind)": the game divides the cost by the price. The price is now 0.0001 (a full tank still costs 0), and a test rejects any 0 divisor.
- Workshop packages: manifest.sii without compatible_versions and display_name (the SCS Workshop Uploader rejects compatible_versions with ERROR 00010 and warns about display_name with WARN 00002). The release `.scs` files keep both for the Mod Manager.
- The zip packages no longer contain directory entries ("[zipfs] error reading a non-directory entry (/def)" in the game log).

Tools:
- `tools/hashfs.py`: HashFS v1/v2 reader (CityHash64 1.0.x).
- `tools/sii_save.py`, `tools/save_money.py`, `tools/save_profile.py`: read encrypted (ScsC/BSII) and text saves and set money, max level and all skills. They back up the save first, and `--restore` puts the backup back.
- `tools/exe_console_commands.py`: shows that the `cheat` console command is not registered in 1.61.
- `tools/top_speed.py`: gear-limited top speed from the real defs.
- `tools/build_mods.py`, `tools/build_workshop.py`: build the mods, the Workshop folders and the release files from the installed game.
