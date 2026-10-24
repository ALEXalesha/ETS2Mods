# Changelog

## 1.2.4 - 2026-10-25

- No Rollover 1.2.1 really stops the tipping: the cargo centre of gravity is 0.5 m lower in all 350 trailer chassis (`cog_cargo_offset_min/max` -> (0, -0.5, 0)). 313 chassis had no such keys: the mod adds them with the mass range 0-30000 kg; 37 had their own. Players reported that the anti-roll bar alone did not work; checked in the game: works with both stability sliders at maximum, not at minimum - the descriptions say so.
- Builder: operations carry their own `require`/`exclude` file filter, new `insert_after_unit`, `or_insert_after_key` from the ATS builder. Law: every trailer chassis block has exactly one of each of the four keys, both points (0, -0.5, 0).

---

- No Rollover 1.2.1 правда не даёт опрокидываться: центр тяжести груза на 0,5 м ниже во всех 350 шасси прицепов (`cog_cargo_offset_min/max` -> (0, -0.5, 0)). У 313 шасси этих ключей не было - мод добавляет их с диапазоном массы 0-30000 кг; у 37 были свои. Игроки писали, что один стабилизатор не работает; проверено в игре: работает с обоими ползунками устойчивости на максимуме, на минимуме - нет, описания об этом говорят.
- Сборщик: у операции свой фильтр файлов `require`/`exclude`, новая `insert_after_unit`, `or_insert_after_key` из сборщика ATS. Закон: в каждом блоке шасси прицепа ровно по одному из четырёх ключей, обе точки (0, -0.5, 0).

## 1.2.3 - 2026-10-24

- Hyper Power 1.2.1: the x0.35 final drive is in every gearbox now. 25 of 195 gearboxes (retarder and overdrive variants) were left stock: tools/cityhash103.py hashed paths over 64 characters with the CityHash 1.0 branch, but HashFS uses the 1.1 branch there, so those game files were invisible. Found in the ATS project, where it hit 83 of 181 gearboxes. Engines were not affected (all 203 paths are shorter), so No Fuel and the torque changes were complete.
- Laws: two long paths with hashes from the game archives, every listed file under def/vehicle has an entry, 195 gearboxes.

---

- Hyper Power 1.2.1: главная пара x0.35 теперь в каждой коробке. 25 из 195 коробок (варианты с ретардером и овердрайвом) оставались заводскими: tools/cityhash103.py считал хеш путей длиннее 64 символов по ветке CityHash 1.0, а HashFS там использует 1.1, и эти файлы игры были невидимы. Найдено в проекте ATS, где так пропало 83 из 181 коробки. Двигателей это не коснулось (все 203 пути короче), поэтому No Fuel и момент были полными.
- Законы: два длинных пути с хешами из архивов игры, у каждого файла из списков def/vehicle есть запись, 195 коробок.

## 1.2.2 - 2026-10-24

Descriptions, plus one new game file in Free Services.

- Free Services: the game now has the Halloween event "country" (`def/country/halloween.sui`); the build picked it up, its fuel is free too. The other mod files are the same as in 1.2.1 apart from the description inside each `.scs`.
- Every Workshop description lists the game files its mod replaces and says that another author's mod with the same file overrides it when higher in the Mod Manager (and the other way round). Players with large mod lists saw our physics, engine, economy and traffic changes disappear under other mods. The line is built from mod.json; tests/test_workshop.py checks it for all ten mods.
- Free Services: в игре появилась событийная «страна» Хэллоуин (`def/country/halloween.sui`), сборка её подхватила - топливо там тоже бесплатное. Остальные файлы модов те же, что в 1.2.1, кроме описания внутри `.scs`.
- В описании каждого мода в Мастерской перечислены файлы игры, которые он заменяет, и сказано, что чужой мод с тем же файлом перекрывает его, если стоит выше в Менеджере модов (и наоборот).

## 1.2.1 - 2026-10-16

Independent review. The ten mods themselves are unchanged (their files are the 1.2.0 build, package version 1.2.0); the tools and one description changed.

- **save_money.py --restore** took the backup of ANOTHER save. The game names its saves autosave, autosave_job, autosave_job_1..9, autosave_drive, autosave_drive_1..9; `--restore --save autosave` looked for `autosave_*` and took the last one by name, and `autosave_job_3_<time>` sorts after `autosave_<time>`. Now only backups named exactly `<save>_<time>` count. Law: `tests/test_save_money.py` SaveFolderTest.
- **The Load screen showed the old money.** A save also keeps the amount in `info.sii` (`info_money_account`, what the Load screen shows; in every real save it equals the bank's money). Both tools wrote only `game.sii`; now `info.sii` gets the same amount.
- Two writes of the same save within one second no longer fail (the backup folder gets a `_2` suffix).
- **Деньги ETS2.bat** did not start from a folder with `%` or `^` in its name ("path not found"): `call` expands a full path a second time. It now goes to its folder and calls `money.bat` by a relative name. Law: BatchFileTest.test_any_folder_name.
- The amount may start with the currency sign, as the game shows roubles: `₽10 000`.
- **Free Services description**: "all 19 ferry and train crossings are free" was true only without map DLCs. The 19 are the crossings of the base game files; crossings that come with map DLCs (Scandinavia, Beyond the Baltic Sea, Iberia, Greece and others) are in those DLCs and keep their price. Workshop text, README and the local mod descriptions corrected.

## 1.2.0 - 2026-10-10

- **Big Money** pays 10x for real. 1.0-1.1 changed `revenue_per_km_base` (15 to 150), which the 1.61 job price does not use, so pay stayed at the vanilla level (field report: freight market about 3,900 RUB/km = 41.5 EUR/km). Now `revenue_coef_per_km` 0.9 to 9, `cargo_market_revenue_coef_per_km` 1.0 to 10, `driver_revenue_coef_per_km` 0.67 to 6.7, `driver_cargo_market_revenue_coef_per_km` 0.70 to 7, `fixed_revenue` 600 to 6000; `revenue_per_km_base` stays 15. Rule and field data (delivery log of a 1.61 save, screenshot offers): `tests/test_pay_law.py`.
- **save_money.py**: the save keeps EUR, the game shows the profile's currency (`g_currency` in the profile's config.cfg, rate from `def/economy_data.sii`). `--set` takes the amount as the game shows it, `--set-eur` writes EUR, `--currency` overrides, every readout shows both; `--profile-dir` and `--backup-dir` for other folders; the written value is read back. Tests: `tests/test_save_money.py`.
- **money.bat / Деньги ETS2.bat**: change the money by double click. It lists the profiles with the money as the game shows it, asks for the new amount in that currency (`10000000000`, `10 000 000 000` or `10 млрд`), waits until the game is closed, backs up and writes the newest save, and prints a big ЗАПИСАНО (written). Field report: "the utility doesn't work at all" - it had been run without `--apply`, which writes nothing. Code: `tools/money_menu.py`; tests: `tests/test_money_menu.py` (also runs both .bat files through cmd.exe).
- **save_money.py**: `--save latest` picks the newest save; a dry run ends with a big "NOTHING WRITTEN, add --apply", a write with "WRITTEN: ... EUR in the file = ... RUB on screen. Now start the game and load the latest save."
- **Steam Cloud**, checked in Steam's own cloud log on the author's PC: after an outside write Steam sees the changed file at the next launch ("SHA mismatch with cache - setting local changes") and uploads it, so the new money stays. A conflict window comes only if the cloud copy changed too; then pick the local files. Both tools say so for a cloud profile.
- Workshop: `steam_changelog.txt` (EN, then RU, CRLF) with the change note for updating an existing item; Big Money has one for 1.2.0. WORKSHOP.md: how to update an item.
- The publish script also replaces the author's personal disk path (git config `publish.privatePath`, any slash and case, also in commit messages); `tests/test_no_personal_path.py` keeps it out of new commits.
- All mods 1.2.0.

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
