# Steam Workshop: how to upload the OpenRoad mods

[English](#english) | [Русский](#русский)

## English

The ten mods are prepared as Workshop folders under the neutral family name "OpenRoad". Nothing is uploaded automatically; you upload them yourself with SCS's official Workshop Uploader.

### 0. Build the folders (once, and again after every change)

```
.venv\Scripts\python tools\build_mods.py
.venv\Scripts\python tools\build_workshop.py
.venv\Scripts\python -m unittest discover -s tests
```

This gives `workshop\NN_OpenRoad_<Name>\` with:
- `upload\`: the mod data folder you pick in the uploader. It holds `versions.sii` and `universal\` (manifest.sii without display_name/compatible_versions, mod_icon.jpg 276x162, mod_description.txt EN+RU, def files);
- `preview.jpg`: the 640x360 Workshop preview image;
- `steam_page.txt`: the title, type tag and page text to paste;
- `steam_description.txt`: only the description, ready to copy whole (Ctrl+A, Ctrl+C). Both files use Windows line breaks, otherwise the uploader's text box glues the paragraphs together;
- `steam_changelog.txt` (only when the mod has a change note for its version): the change note for an Update, see step 6.

The tests check the uploader's rules (layout, manifest fields, icon size, UTF-8 description, "SiiNunit" headers, no unreferenced files), check for zero values the game divides by, and check that no personal data is included.

### 1. Turn on Tools in the Steam library

Steam -> Library -> the filter above the game list (it says "Games") -> tick **Tools**.

### 2. Install the uploader

In the Tools list, find SCS's Workshop Uploader for Euro Truck Simulator 2 (search for "Workshop Uploader"), install it and start it from Steam.

### 3. Upload one mod

Following the SCS modding wiki ("How to upload new mod?"):
1. Select the game: Euro Truck Simulator 2.
2. Press **New**.
3. Mod data folder: `workshop\NN_OpenRoad_<Name>\upload`. Pick the `upload` folder, not `universal`.
4. Preview image: `workshop\NN_OpenRoad_<Name>\preview.jpg`.
5. Mod name: the TITLE from `steam_page.txt`.
6. Visibility: **Private** for the first test.
7. Description: open `steam_description.txt`, copy all of it and paste (at least 50 characters).
8. Type tag: the TYPE TAG from `steam_page.txt` (Physics, Others or AI Traffic, or the closest one the uploader offers).
9. Change note: e.g. "1.0 - first release for game 1.61".
10. Press **Upload**. The uploader validates the folder first and shows an error if something is wrong.

### 4. Test, then publish

- Subscribe to your own Private item and turn it on in the Mod Manager.
- Turn off the local `alexey_*.scs` mods with the same function, so the same mod does not run twice.
- Check it in game (see the README for what to check per mod).
- Then set the visibility to **Friends only** or **Public**, on the item's Steam page or with **Update** in the uploader.

Suggested upload order: start with a small one as a test (10 More Traffic), then the rest in any order. Order does not matter for uploading. What matters is the order in the Mod Manager: 01 at the top, 10 at the bottom, with 02 Super Power off when 01 Hyper Power is on.

### 5. After a game update

1. Rebuild (step 0). The build stops with an error if SCS renamed a parameter. Workshop packages carry no `compatible_versions` and no `display_name` in manifest.sii: the uploader rejects the first (ERROR 00010, versions belong in versions.sii) and warns about the second (WARN 00002, the name comes from the Steam page). The game version in the description is taken from the game files automatically.
2. In the uploader choose **Update** (not New), pick the existing item, choose the new `upload` folder, write a change note such as "Updated for game 1.62", then press Upload.
3. The Workshop item keeps its ID, subscribers and comments.

### 6. Update an existing item (example: Big Money 1.2.0)

1. Rebuild (step 0). The mod's folder then also has `steam_changelog.txt`: the change note, English then Russian.
2. Start the Workshop Uploader from the Steam library (Tools), choose Euro Truck Simulator 2.
3. Choose **Update** (not New) and pick the existing item, "OpenRoad: Big Money".
4. Mod data folder: `workshop\03_OpenRoad_Big_Money\upload` again. Preview image: `preview.jpg` from the same folder.
5. Description: paste `steam_description.txt` again if the text changed (for 1.2.0 it did).
6. Change note: open `steam_changelog.txt`, Ctrl+A, Ctrl+C, paste.
7. Leave the visibility as it is and press **Upload**. Subscribers get the new version automatically the next time Steam updates the game's Workshop items.

## Русский

Десять модов подготовлены как папки для Мастерской под нейтральным названием серии «OpenRoad». Сам я ничего не выкладывал; загружать их нужно самому через официальный загрузчик SCS.

### 0. Собрать папки (один раз и после каждой правки)

```
.venv\Scripts\python tools\build_mods.py
.venv\Scripts\python tools\build_workshop.py
.venv\Scripts\python -m unittest discover -s tests
```

Получится `workshop\NN_OpenRoad_<Имя>\`:
- `upload\` - папка данных мода, её выбирать в загрузчике. Внутри `versions.sii` и `universal\` (manifest.sii, иконка 276x162, описание EN+RU, def-файлы);
- `preview.jpg` - превью для Мастерской 640x360;
- `steam_page.txt` - название, тег типа и текст для страницы;
- `steam_description.txt` - только описание, копировать целиком (Ctrl+A, Ctrl+C). Оба файла с переводами строк Windows, иначе поле загрузчика склеивает абзацы;
- `steam_changelog.txt` (только если у мода есть заметка для его версии) - заметка об изменениях для обновления, см. шаг 6.

Тесты проверяют правила загрузчика, отсутствие нулей, на которые игра делит, и отсутствие личных данных.

### 1. Включить «Инструменты» в библиотеке Steam

Steam -> Библиотека -> фильтр над списком игр («Игры») -> отметить **Инструменты**.

### 2. Установить загрузчик

В списке инструментов найти загрузчик Мастерской от SCS для Euro Truck Simulator 2 (поиск «Workshop Uploader»), установить и запустить из Steam.

### 3. Загрузить мод

1. Выбрать игру Euro Truck Simulator 2.
2. Нажать **New**.
3. Папка данных мода: `workshop\NN_OpenRoad_<Имя>\upload`. Именно `upload`, не `universal`.
4. Превью: `preview.jpg` из той же папки.
5. Название: TITLE из `steam_page.txt`.
6. Видимость: для первой проверки **Private** (скрытый).
7. Описание: открыть `steam_description.txt`, скопировать всё и вставить (не меньше 50 символов).
8. Тег типа: TYPE TAG из `steam_page.txt` (Physics, Others, AI Traffic или ближайший из предложенных).
9. Заметка об изменениях: например «1.0 - первая версия для игры 1.61».
10. Нажать **Upload**. Загрузчик сначала проверит папку и покажет ошибку, если что-то не так.

### 4. Проверить и открыть

- Подписаться на свой скрытый мод и включить его в Менеджере модов.
- Выключить локальные `alexey_*.scs` с той же функцией, чтобы мод не работал дважды.
- Проверить в игре (что смотреть - в README).
- Потом поставить видимость **Friends only** или **Public** на странице мода в Steam или через **Update** в загрузчике.

Порядок загрузки: сначала маленький для пробы (10 More Traffic), потом остальные в любом порядке. Для загрузки порядок не важен. Важен порядок в Менеджере модов: 01 сверху, 10 снизу, а 02 Super Power выключить, если включён 01 Hyper Power.

### 5. После обновления игры

1. Пересобрать (шаг 0). Если SCS переименует параметр, сборка остановится с ошибкой. В manifest.sii пакетов Мастерской нет `compatible_versions` и `display_name`: загрузчик отвергает первое (ERROR 00010, версии - в versions.sii) и предупреждает о втором (WARN 00002, название берётся со страницы Steam). Версия игры указана в описании, она берётся из файлов игры при сборке.
2. В загрузчике выбрать **Update** (не New), выбрать уже загруженный мод, указать новую папку `upload`, написать заметку «Обновлено для игры 1.62» и нажать Upload.
3. ID мода, подписчики и комментарии сохраняются.

### 6. Обновить уже загруженный мод (пример: Big Money 1.2.0)

1. Пересобрать (шаг 0). В папке мода появится ещё `steam_changelog.txt` - заметка об изменениях, сначала по-английски, потом по-русски.
2. Запустить загрузчик Мастерской из библиотеки Steam («Инструменты»), выбрать Euro Truck Simulator 2.
3. Нажать **Update** (не New) и выбрать уже загруженный мод «OpenRoad: Big Money».
4. Папка данных мода: снова `workshop\03_OpenRoad_Big_Money\upload`. Превью: `preview.jpg` из той же папки.
5. Описание: вставить `steam_description.txt` заново, если текст поменялся (в 1.2.0 поменялся).
6. Заметка об изменениях (Change note): открыть `steam_changelog.txt`, Ctrl+A, Ctrl+C, вставить.
7. Видимость не трогать, нажать **Upload**. Подписчики получат новую версию сами, когда Steam в следующий раз обновит моды игры.
