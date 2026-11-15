# GroundTwin — обзор сайта и кода

Отчёт составлен строго по коду репозитория (состояние на коммит `b1e8693`, 57 коммитов). Сайт на английском, отчёт на русском.
Адрес GitHub Pages: `https://zhureswe.github.io/groundtwin/`. Сайт Framer (обложка) в коде упомянут один раз: в `docs/embed/globe.html` и `framer/Analogs.tsx` есть ссылки на `https://true-memory-123862.framer.app/analog?id=…`.

---

## 1. Вкладки, стек и путь пользователя

### 1.1 Стек
| Слой | Что используется | Где |
|---|---|---|
| Хостинг | GitHub Pages, папка `/docs`, без сервера | `docs/` |
| Разметка и логика | чистые HTML + CSS + JavaScript (ES2020), без сборщика | `docs/index.html`, `docs/assets/app.js`, `docs/embed/*.html` |
| Библиотеки с CDN | Leaflet 1.9.4 (2D-карта), Chart.js 4.4.1 (радар-диаграмма), KaTeX 0.16.9 (формулы) — cdnjs; CesiumJS 1.121.0 (3D-глобус) — jsDelivr | `index.html`, `embed/globe.html`, `embed/prototype.html` |
| Шрифты | Google Fonts: Space Grotesk (заголовки), Inter (текст), JetBrains Mono (подписи) | все страницы |
| Данные | статические JSON в `docs/data/`, которые пишет Python-пайплайн | `pipeline/*.py` |
| Пайплайн | Python 3.12: numpy, pandas, rasterio, rioxarray, pyproj, shapely, scipy, matplotlib, earthengine-api, reverse_geocoder, markdown | `requirements.txt` |
| Внешние данные при работе страницы | тайлы NASA GIBS, OpenStreetMap Nominatim (только Scout, по запросу пользователя) | `app.js`, `globe.html`, `scout.html` |
| Framer | код-компонент `AnalogList` / `AnalogDetail` (React + TypeScript) | `framer/Analogs.tsx` |

### 1.2 Вкладки главного сайта (`docs/index.html`)
Одностраничный сайт с роутером по `#hash` (`show()` в `app.js`). Меню `#navlinks`:

| Пункт меню | Адрес | Что внутри |
|---|---|---|
| (логотип) Home | `#home` | заголовок «Where does Earth echo like the Moon?», 4 числа-итога (`renderHome`), 3 карточки модулей, «Why it matters» |
| Radar Twin | `#radar` | карта южного полюса Луны (SVG), карточка кратера, таблица всех целей, «земная линейка» CPR, таблица m-χ/DOP, главный вывод |
| Explore Earth | `#explore` | Leaflet-карта сходства, выбор цели и режима, карточка клетки с радар-диаграммой, топ-10, «Top 5 by formula», 3 выделенные карточки |
| Mars Field Twin | `#mangystau` | ранг Мангистау для Gale/Jezero, 6 снимков Sentinel-2, таблица 6 мест, таблица «Mangystau vs Utah vs Mars», PCA-график, таблица «что похоже / что нет» |
| Method | `#method` | формулы (KaTeX), Lift, слепой тест, длина волны (Рэлей), таблица данных, Limitations |
| About | `#about` | команда Code Influence, название челленджа, ссылка на GitHub и PDF статьи, Use of AI, кредиты |
| How it works | `embed/analog-engine.html` | отдельная страница |
| Scout | `embed/scout.html` | отдельная страница |
| Moon Ice | `embed/moon-ice.html` | отдельная страница |
| 3D Globe | `embed/globe.html` | отдельная страница |

На телефоне меню сворачивается в бургер (`#menu`). Помощник «Ask GroundTwin» (`assets/ask.js`) подключён на главной и на всех embed-страницах, открытых без `?embed=1`.

### 1.3 Встраиваемые страницы (`docs/embed/`)
Каждая работает сама, параметр `?embed=1` скрывает шапку и подвал (`common.js` ставит класс `is-embed`). Предназначены для Embed во Framer.

| Файл | Назначение |
|---|---|
| `analog-engine.html` | «How we find Earth twins»: проблема → 7 карт → процентили → профили целей → веса → живой расчёт формулы → 8 мест → проверка → ограничения → Scout во фрейме |
| `analogs.html` | 8 мест: «4 famous field analogs» + «Our 4 picks», одинаковые карточки |
| `globe.html` | 3D-глобус Cesium + переключатель на 2D-карту сходства (тот же код, что Explore) |
| `moon-ice.html` | разбор второго направления по шагам: проблема → проверка на Земле → 3 слоя NASA → подсчёт улик → таблица → ограничения |
| `prototype.html` | вкладки «Scout (ask the formula)» (iframe), «Analog Engine», «Radar Twin» (тот же код `app.js`) |
| `scout.html` | чат-калькулятор формулы для любого места |
| `ask.html` | помощник Ask GroundTwin на всю страницу (`data-mode="page"`) |
| `../globe.html` | старая ссылка, перенаправляет на `embed/globe.html` |

### 1.4 Путь пользователя (User Flow)
1. **Home** → 4 числа и кнопки «Decode the Moon's radar →» (#radar) и «Find Earth twins» (#explore).
2. **Направление 1:** How it works (как считается) → Analogs (8 мест с объяснением) → 3D Globe (те же места на глобусе, 2D-карта всех клеток) → Scout (проверить своё место).
3. **Направление 2:** Moon Ice (история по шагам) или Radar Twin (клик по кратеру → улики → линейка).
4. **Мангистау:** Mars Field Twin.
5. **Доверие:** Method (формулы, проверка, ограничения) → About (команда, AI, кредиты) → PDF статьи.
6. В любой момент: кнопка «Ask GroundTwin» внизу слева.

---

## 2. Что добавлено, что убрано, где заглушки

### 2.1 Добавлено за время проекта (по истории коммитов)
- Реальные данные вместо демо: все `docs/data/*.json` имеют `demo: false`, жёлтый баннер DEMO скрыт.
- Модуль Мангистау (вместо Аральского моря), 6 мест с источниками координат.
- Analog Engine (сетка 0,5°, 60 215 клеток суши), валидация Lift и средний ранг, слепой тест, PCA, сравнение с Ютой и Девоном.
- Компактная поляриметрия m-χ и DOP, проверка критерия CPR > 1 и DOP < 0,13, порог Рэлея.
- Доля холодного дна (< 110 K) для каждого кратера.
- Помощник Ask GroundTwin (45 ответов, 7 категорий, режим сравнения).
- Тема «тёмный космос + чертёж», embed-страницы для Framer, 3D-глобус, Scout, Moon Ice, How it works.
- От подруги: известные полевые аналоги (`15_famous_analogs.py`), лучшие места по странам (`16_country_top.py`), карты «Breakdown» (`17_breakdown_maps.py`, 152 PNG в `docs/assets/img/bd/`), мозаика LROC WAC южного полюса, Framer-компоненты, ссылки на источники в подвалах.
- Статья (6 стр., PDF), README, тексты сабмишна, лицензия MIT.

### 2.2 Убрано
- Аральское море (заменено Мангистау).
- Старый встроенный справочник в `app.js` (вынесен в `assets/ask.js`).
- Фон CARTO (требовал ключ) → NASA GIBS Blue Marble.
- Фраза «×3,6 better than chance» (не подтверждалась данными).
- Слово «probability» про наши оценки (заменено на «similarity score» / «evidence score»).
- Имена участниц не публикуются (только «Team Code Influence»).
- Плашка Мангистау под аналогами (Мангистау теперь внутри «Our 4 picks»).

### 2.3 Заглушки и незаполненное
| Где | Что |
|---|---|
| `submission/project_page.md` (и шаблон) | `[Demo link — 7 slides, public Google Drive / GitHub]` |
| `README.md` (и шаблон) | «Demo: [link to be added]» |
| `docs/index.html` | баннер DEMO — скрыт, пока все JSON имеют `demo:false` |
| `app.js` (`renderMangystau`) | текст-заглушка «Sentinel-2 true-colour views … will appear here» — показывается, только если в `mangystau.json` нет картинок (сейчас картинки есть) |
| `docs/data/analog_top.json` | файл больше нигде не читается сайтом (остался от T4) |

---

## 3. Тема, интерфейс, 2D/3D-карты и графики

### 3.1 Тема (`assets/style.css`, `embed/embed.css`, `assets/ask.css`)
- Фон `#05070d`, тонкая сетка 40 × 40 px (`linear-gradient`), мягкие радиальные свечения бирюзой и оранжевым.
- Цвета: бирюза `#4fd1e8` (Луна, лёд), оранжевый `#ff6a3d` (Марс), зелёный `#6fcf97` (совпадает), розовый `#f08a7a` (не совпадает).
- HUD: уголки у карточек (`.card::before/::after`), линии-заголовки секций `.hud` с градиентной чертой.
- Шрифты: Space Grotesk (заголовки), Inter (текст), JetBrains Mono (подписи, бирки, таблицы).
- Анимации лёгкие: появление страницы (`fade`), пульс кнопки помощника, полоски критериев растут (`transition`), «стопка» слоёв в Moon Ice наклонена через `rotateX`. Есть `prefers-reduced-motion`.
- Адаптивность: сетки с `minmax(0, 1fr)`, `min-width: 0` у детей сеток, прокрутка таблиц и формул внутри блоков. На 390 px нет горизонтальной прокрутки (проверено).
- Общее правило `[hidden] { display: none !important }`.

### 3.2 2D-карты
- **Explore / 2D на глобусе** (`app.js`, Leaflet): подложка NASA GIBS `BlueMarble_ShadedRelief_Bathymetry` (уровень 8, прозрачность 0,55). Поверх — картинка-оверлей, нарисованная в `<canvas>` 2048 × 2048 в проекции Меркатора: каждая клетка 0,5° окрашена по рангу (нижние 50% прозрачны, далее тёмно-синий → бирюза → белый для лучшего 1%). Белые кружки — известные аналоги (зелёная заливка, если в топ-10%). Клик по суше → карточка клетки.
- **Карта южного полюса Луны** (Radar Twin, `drawPolar`): своя SVG в полярной проекции до 81,5° ю.ш., кружки целей, размер и цвет по evidence score (0–3), горы серые («n/a»).
- **Земная линейка** (`drawRuler`, SVG; в Moon Ice — HTML-полоски): медиана CPR и межквартильный размах по каждому земному месту, пунктир CPR = 1, белые линии выбранного кратера (внутри / снаружи).

### 3.3 3D-глобус (`embed/globe.html`)
- CesiumJS без Cesium ion: `Cesium.Ion.defaultAccessToken = ''`, подложка — `UrlTemplateImageryProvider` с NASA GIBS Blue Marble, приближение ограничено (`minimumZoomDistance = 60 000 м`).
- 9 булавок (`PinBuilder`), 5 групп с галочками: «Famous field analogs · Moon/Mars», «Our picks · Moon», «Our pick · Mars», «New candidate · Mangystau».
- Клик по булавке → панель: S, ранг, «top X% of land cells», 7 полосок, чипы, «What Earth cannot reproduce», кнопки «Details, satellite images and sources →» (Framer), Google Earth, NASA Moon/Mars Trek.

### 3.4 Графики
- **Радар-диаграмма** (Chart.js) в карточке клетки: 7 процентилей места против профиля цели.
- **Полоски критериев** (`GTE.bars` в `common.js`): заполнение = процентиль места, белая риска = профиль цели; цвет зелёный/жёлтый/розовый по s_i.
- **PNG из пайплайна**: `analog_pca.png` (PCA, PC1 31%, PC2 29%), `earth_cpr_by_class.png`, `moon_vs_earth_cpr.png`, `moon_south_pole_map.png` (в статье), 6 снимков Мангистау.
- **Framer «Breakdown»** (`framer/Analogs.tsx`): «Three maps, one place» — снимок Sentinel-2 (EOX s2cloudless, для Антарктиды — Blue Marble), рельеф ASTER GDEM (NASA GIBS), карта оценки S; режим «7 layers» — 7 карт совпадения по критериям (PNG из `17_breakdown_maps.py`), «разлёт» слоёв с повтором.

---

## 4. Направление 1 — аналоги на Земле

### 4.1 Слои (7 критериев) — `pipeline/04_analog_engine.py`, `analog_grid.json`
Сетка 0,5°, суша 60° ю.ш. – 90° с.ш. (Антарктида исключена), период 2015–2024, Google Earth Engine.

| Критерий | Данные | Направление «экстремальности» |
|---|---|---|
| aridity (Dry) | NASA GPM IMERG V07, среднегодовые осадки | меньше осадков |
| barren (No plants) | MODIS MOD13A2 NDVI, годовой максимум | меньше растений |
| thermal_range (Day–night swing) | MODIS MOD11A2 LST день − ночь | больше перепад |
| cold (Cold) | MODIS MOD11A2 LST ночь, 5-й перцентиль | холоднее |
| dust (Dust) | MODIS MOD08_M3 AOD 550 нм | пыльнее |
| roughness (Rough terrain) | USGS GMTED2010, std высоты | шероховатее |
| elevation (High altitude) | USGS GMTED2010, средняя высота | выше |

Маска суши — MODIS MCD12Q1. У 2 464 клеток нет данных о пыли → нейтральное 0,5.
Каждое значение переводится в процентиль p ∈ [0, 1]. Формула: s_i = 1 − |p_i − t_i|, S = Σ w_i s_i / Σ w_i.
Цели (`targets.json`): Moon — south pole base, Mars — Jezero, Mars — Gale. Режимы весов: Science, Rover operations, Base construction, Ice & resources.
Ранг = 1 + число клеток с бо́льшим S; «top X% of land cells» = ранг / 60 215.

### 4.2 Локации в коде

**Восьмёрка (версия B)** — `analogs8.json` (`18_analogs8.py`), `analogs.html`, шаг 6 `analog-engine.html`, глобус, Framer:

| Блок | Место | Цель | S | Ранг | Доля |
|---|---|---|---|---|---|
| 4 famous field analogs | Atacama Desert, Chile | Mars (Gale) | 0.841 | #4 728 | top 7.9% |
| | Death Valley, USA | Mars | 0.793 | #7 166 | top 11.9% |
| | Devon Island, Canada (координаты Haughton) | Mars | 0.790 | #7 305 | top 12.1% |
| | Utah desert, USA (координаты MDRS) | Mars | 0.768 | #8 467 | top 14.1% |
| Our 4 picks | Mangystau, Kazakhstan (среднее 6 клеток) | Mars | 0.822 | #5 729 | top 9.5% |
| | Xinjiang, China | Moon | 0.925 | #1 | top 0.002% |
| | Govi-Altai, Mongolia | Moon | 0.904 | #18 | top 0.03% |
| | Xinjiang, China | Mars | 0.941 | #1 | top 0.002% |

**Другие наборы мест в данных:**
- `famous_analogs.json` (10): Atacama, Death Valley, Devon Island, Hawaiʻi lava fields, Lanzarote (не оценён), Río Tinto, McMurdo Dry Valleys (не оценён, Антарктида вне сетки), Utah desert, Iceland lava fields, Mangystau.
- `country_top.json`: лучшее место на страну, ≥ 600 км. Луна: Xinjiang, Govi-Altai, Ladakh, Catamarca, Erongo. Марс: Xinjiang, Illizi, Aswan, Tibesti, Drâa-Tafilalet. Названия — GeoNames (`reverse_geocoder`).
- `showcase.json` (вкладка Explore на главной): «Top 5 by formula» с названиями FAO GAUL и 3 выделенные карточки — Cinder Lake / Meteor Crater (Аризона), MDRS / San Rafael Swell (Юта), Мангистау.
- `validation.json`: 16 известных аналогов (NASA Planetary Analog Explorer, USGS TADP, эталоны MDRS, San Rafael Swell, Devon, Haughton).
- `mangystau.json`: Torysh, Sherkala, Karagiye, Karynzharyk, Bozzhyra, Tuzbair (источники: Википедия, OSM).

### 4.3 Проверка
Lift в топ-10% слабый (Science: Луна ×2,00, Gale ×0,91, Jezero ×0,00). Средний ранг известных марсианских аналогов: Gale — лучшие 21,3% (p = 0,001), Jezero — 24,4% (p = 0,003). Слепой тест: 7 из 11 марсианских (шанс ≈ 1,1, p = 2·10⁻⁵), 8 из 13 всех.

---

## 5. Направление 2 — Radar Twin (лёд на Луне)

### 5.1 Идея и код
Высокий CPR дают и лёд, и камни. Канадский RCM имеет ту же гибридную компакт-поляриметрию, что Mini-RF, поэтому CPR меряется на Земле там, где известна правда (`01_earth_radar.py`), и сравнивается с кратерами (`02_moon_radar.py`).

**Земля (RCM, C-диапазон 5,55 см)** — `earth_cpr.json`: 8 мест, CPR = RR/RL, блоки 5 × 5 пикселей, локальный угол 30–60°, зимние снимки.
- Гладкие: Athabasca Dunes, Great Sand Hills, Regina Plain — медиана класса 0,21.
- Камни/лава: Nisga'a Lava Bed, Edziza Lava Field — 0,52.
- Лёд: Columbia, Clemenceau, Wapta Icefields — 1,44.
- Для Devon Ice Cap, Haughton, Penny Ice Cap открытых сцен RCM нет.

**Луна — три карты NASA LRO** (слои в Moon Ice):
| Слой | Данные | Улика (+1 к оценке) |
|---|---|---|
| Mini-RF radar | глобальная мозаика CPR 128 ppd (PDS) | CPR внутри (r < 0,8 R) / снаружи (1,2–2 R) > 1,2 |
| Diviner temperature | Polar Resource Product (dlre_prp_south) | медиана годового Tmax дна < 110 K |
| LOLA terrain | полярная DEM 80 м | медианный уклон дна < 8,12° (медиана по кратерам) |

**Цели** (`moon_targets.json`, координаты — IAU Gazetteer): 12 целей, из них 10 кратеров — Shackleton, Haworth, Shoemaker, Faustini, Cabeus, de Gerlache, Sverdrup, Nobile, Cabeus B, Slater; 2 горы без оценки — Mons Malapert, Mons Mouton. Регионы Artemis III привязаны к объектам IAU.
Итог: 5 из 10 кратеров с оценкой ≥ 2 (Shackleton, Haworth, Shoemaker, Cabeus, Cabeus B). Shackleton: CPR 0,69 / 0,38, Tmax 93 K, 93% дна холоднее 110 K, оценка 2/3.

**Вторая радарная проверка** (`08_polarimetry.py`, `polarimetry.json`): Стокс-параметры, m (DOP), χ. Критерий CPR > 1 и DOP < 0,13 проходят: лёд 1,69%, лава 1,20%, гладкие 0,04% → «одной радарной улики мало». χ разделяет классы лучше (−41°, −28°, +9°).
**Длина волны** (`09_wavelength.py`): порог Рэлея h = λ / (8 cos θ): RCM 0,80–1,39 см, Mini-RF 2,35 см; сравнивается порядок классов, а не абсолютные значения.

### 5.2 Интерфейс
- Radar Twin (`#radar` и вкладка в прототипе): клик по кратеру → карточка с 3 уликами ✓/✕, «на какое земное место похоже эхо», линейка.
- Moon Ice: выпадающий список кратеров (по умолчанию Shackleton), три улики ✅/❌, «evidence score X / 3», таблица с сортировкой по оценке, клик по строке выбирает кратер.
- Framer: картинка мозаики LROC WAC (`moon_south_pole_lroc_wac.jpg`, NASA/GSFC/ASU) на страницах лунных мест.

---

## 6. Чаты (все без живого ИИ, без API и сервера)

### 6.1 Ask GroundTwin — `docs/assets/ask.js` + `ask.css` (+ `embed/ask.html`)
- **Подключение одной строкой** `<script src=".../assets/ask.js" defer>`. Скрипт сам вычисляет базовый адрес из своего `src`, подгружает `ask.css`, шрифты и `data/faq.json` по абсолютным ссылкам. Атрибуты: `data-mode="page"` (на весь экран, без кнопки), `data-site` (куда ведут «Open on site»).
- **Интерфейс:** круглая кнопка внизу слева (left 20px, bottom 20px); панель слева, на телефоне (≤ 480 px) на весь экран. Приветствие «Hi! I'm the GroundTwin guide…», 7 вкладок-категорий (About the project, Using the site, Analogs, Moon radar, Data & NASA sources, Method & limits, Team & AI use), до 6 подсказок, пузыри как в чате, подпись «Not a live AI…». Enter — отправить, Esc — закрыть. Класс `gta-has-launch` добавляет подвалам отступ, чтобы кнопка их не закрывала.
- **Поиск ответа:** вопрос разбивается на слова, стоп-слова отбрасываются. Очки: многословное ключевое слово целиком +3, совпадение со словом-ключом или общий префикс (> 3 букв) +2, слово есть в тексте вопроса +1. Порог 2. Показывается лучший ответ и до 3 «Related».
- **Ответ:** метка «Official source» / «Our result» / «Our method», текст, кнопки-ссылки на источники, «Open on site →», 👍/👎 (только визуально, ничего не отправляется).
- **Режим сравнения:** срабатывает на «compare / vs / versus / difference between» или по кнопке «Compare two places» (две выпадашки). Сущности собираются из JSON:
  - места-аналоги (`showcase`, `explanations`, `references`) → таблица 7 критериев + S, косинус, ранг + 3–4 предложения по шаблону + «What Earth cannot reproduce»;
  - лунные цели (`moon_targets`) и земные радарные места (`earth_cpr`) → таблица своих показателей.

  Сокращения понимаются (MDRS), «Cabeus B» не путается с «Cabeus». Разные типы мест не сравниваются, об этом пишется честно.
- **Нет ответа:** «I don't know yet — try one of these:» + подсказки + ссылка на GitHub.
- **Ответы** генерирует `pipeline/11_faq.py`, числа в них подставляются из JSON. 45 ответов, пометка «Answers prepared with AI assistance from our verified data».

### 6.2 GroundTwin Scout — `docs/embed/scout.html`
- **Это калькулятор формулы в виде чата.** Грузит `analog_grid`, `targets`, `moon_targets`, `showcase`, `famous_analogs`, `validation`, `earth_cpr`, `mangystau`.
- **Распознавание места:**
  1. координаты в тексте;
  2. справочник мест из наших JSON (Мангистау — группа из 6 мест: среднее S, медианный ранг);
  3. иначе геокодер OpenStreetMap Nominatim.
- **Распознавание цели и режима:** по словам. «Jezero», «Mars/Gale», «Moon» выбирают цель; «rover», «build», «ice/water» — режим. Можно выбрать и в выпадашках.
- **Расчёт:** ищется клетка 0,5° (или соседняя), S считается в браузере, ранг — бинарным поиском по отсортированным S всех клеток. Оценка-ярлык: топ 1% — Excellent, 10% — Strong, 25% — Moderate, иначе Weak.
- **Ответ:** «Match %» (S × 100), ранг, доля суши, 7 полосок, Matches / Partly / Differs, «Why it fits / Why it doesn't fit» (общая функция `GTE.reasons`), «What Earth cannot reproduce», Google Earth / Trek, блок «How was this computed?».
- **Дополнительные режимы:** кратер (оценка из `moon_targets.json`), «Top places…» (топ-5 пересчитывается вживую, ≥ 600 км), сравнение двух мест.

### 6.3 Других чатов нет
Живых ИИ-моделей, ключей API или серверных вызовов в коде нет. Все тексты либо фиксированные, либо собраны шаблоном из чисел.

---

## 7. Файлы данных и правила NASA Space Apps

### 7.1 Данные (`docs/data/`, все `demo: false`)
| Файл | Скрипт | Кто читает |
|---|---|---|
| `earth_cpr.json` | 01 + export | app.js, ask.js, moon-ice, scout |
| `moon_targets.json` | 02 + export | app.js, ask.js, moon-ice, scout |
| `mangystau.json` | 03 | app.js, analog-engine, globe, scout, Framer |
| `analog_grid.json` (≈ 3,4 МБ) | 04 | app.js, analog-engine, scout, Framer |
| `analog_top.json` | 04 | **никто** |
| `targets.json` | команда | почти все страницы |
| `validation.json` | 05 | app.js, analog-engine, scout, Framer |
| `references.json` | 06 | app.js, ask.js |
| `blind_test.json` | 07 | app.js, analog-engine |
| `polarimetry.json` | 08 | app.js, moon-ice |
| `wavelength.json` | 09 | app.js, moon-ice |
| `showcase.json` | 10 | app.js, ask.js, analog-engine, scout, Framer |
| `faq.json` | 11 | ask.js |
| `explanations.json` | 13 | app.js, ask.js, Framer |
| `famous_analogs.json` | 15 | analog-engine, globe, scout, Framer |
| `country_top.json` | 16 | globe, Framer |
| `analogs8.json` | 18 | analogs, analog-engine |

Также `data/` (копии, PNG для статьи), `paper/numbers.md` (106 чисел статьи с ключами JSON), `paper/number_audit.md` (сверка сайт ↔ JSON).

### 7.2 Правила
- **Логотипы NASA:** в HTML/CSS/JS/TSX нет картинок или упоминаний «meatball», «NASA logo», «insignia». Логотип GroundTwin — собственный SVG (два круга). Внизу 3D-глобуса виден стандартный логотип Cesium (атрибуция библиотеки), не NASA.
- **ИИ-картинки:** не используются. Все картинки — графики из данных, спутниковые снимки (Sentinel-2, GIBS, LROC) с подписями-кредитами, скриншот собственного сайта.
- **RCM:** строка «RADARSAT Constellation Mission Imagery © Government of Canada (2025). RADARSAT is an official mark of the Canadian Space Agency.» есть в About (`index.html`), в подвалах `moon-ice.html` и `prototype.html`, в README, статье и сабмишне. В `scout.html`, `analogs.html`, `analog-engine.html` и `globe.html` её нет — там данные RCM не показываются.
- **Use of AI** (одинаковый текст): «We used Claude (Anthropic) as a tool for code, data processing and drafting and editing English texts. The idea, methods, decisions, result checks and design are ours. No AI-generated images or videos.» — в About, справочнике, README, статье, сабмишне. Метки «AI-written from our data» стоят на объяснениях мест, пометка «prepared with AI assistance» — на справочнике. В каждом файле кода есть комментарий «Code written with assistance from Claude (Anthropic)…».
- **«Не одобрено NASA»:** «GroundTwin is not endorsed by NASA or any space agency» в About и подвалах.
- **Данные NASA** используются: LRO Mini-RF, Diviner, LOLA, MODIS, GPM, GIBS, Planetary Analog Explorer, Moon/Mars Trek.

---

## 8. Чего нет, баги и сценарий демо

### 8.1 Чего нет на сайте
- Ссылки на демо (7 слайдов) — заглушка в README и сабмишне.
- Имён участниц и фото (намеренно).
- Радарного близнеца для Марса, S-диапазона NISAR (только в планах).
- Мобильного приложения, входа, сервера, живого ИИ.
- Версий на казахском и русском (только в планах).
- Данных RCM для Арктики (Devon, Haughton, Penny) — открытых сцен нет.

### 8.2 Найденные несоответствия и баги (по коду)
1. **Два набора «лучших мест».**
   - Explore на главной (`showcase.json`): «Top 5 by formula», названия FAO GAUL («Xinjiang Uygur Zizhiqu») и карточки Cinder Lake / MDRS / Мангистау.
   - Analogs, глобус и Framer (версия B): `country_top.json` с названиями GeoNames («Xinjiang») и другая восьмёрка.

   Числа совпадают, но списки и названия разные.
2. **README и статья** говорят о «Training references» (Cinder Lake, Meteor Crater, MDRS, San Rafael Swell) и топ-5, а не о восьмёрке версии B.
3. **Ранг в Scout** может отличаться на несколько мест от пайплайна (Мангистау #5 735 против #5 729), потому что `analog_grid.json` хранит процентили с 3 знаками. Scout пишет об этом в «How was this computed?»; «top 9.5%» совпадает.
4. **«Open on site»** в Ask GroundTwin ведёт на `index.html#…` GitHub Pages, а не на страницы Framer (настраивается атрибутом `data-site`).
5. **Адрес Framer** `true-memory-123862.framer.app` зашит в `globe.html` и `Analogs.tsx` — при смене домена ссылки «Details» сломаются.
6. **Подпись внутри `analog_pca.png`** — «7 percentile features», а на сайте везде «7 criteria» (PNG не перерисован).
7. **`analog_top.json`** не используется.
8. **Cabeus:** медиана Tmax 225 K → не проходит улику «холодно», хотя 17% дна < 110 K и LCROSS нашёл воду. Объяснено в Limitations, правило не менялось.
9. **Lift слабый** (Jezero ×0,00) — честно показан, но жюри может спросить.
10. **Объём загрузки:** Explore, 2D-карта, Scout и How it works загружают `analog_grid.json` ≈ 3,4 МБ; на медленном интернете первые секунды пусто.
11. **Scout отправляет текст запроса** в OpenStreetMap Nominatim, если места нет в наших файлах (внешний сервис, ограничения по частоте).

### 8.3 Сценарий демо на 1 минуту
| Время | Где | Что сказать / показать |
|---|---|---|
| 0:00–0:10 | Home | «Where does Earth echo like the Moon? GroundTwin uses Earth as the twin of the Moon and Mars.» Показать 4 числа. |
| 0:10–0:25 | Analogs | «Seven NASA criteria, one formula for all 60,215 land cells.» Открыть карточку Мангистау: S 0.82, top 9.5%, полоски, «Why it fits / doesn't». Рядом Atacama — известный аналог, top 7.9%. |
| 0:25–0:35 | 3D Globe | Покрутить глобус, кликнуть Xinjiang — #1 для Луны и Марса. |
| 0:35–0:45 | Scout | Ввести «Compare Mangystau and Death Valley for Mars» — живой расчёт. |
| 0:45–0:55 | Moon Ice | «On Earth the newest lunar ice rule barely separates ice (1.69%) from lava (1.20%) — so we combine three NASA maps.» Shackleton: 2/3. |
| 0:55–1:00 | Ask GroundTwin | Кнопка внизу слева → «How did you use AI?». «Everything open on GitHub; scores are similarity and evidence, not proof.» |
