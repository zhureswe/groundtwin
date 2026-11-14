# GroundTwin — инструкции для Claude Code

> Этот файл Claude Code читает автоматически. Он описывает весь проект, порядок работы и правила.
> Команда: **Code Influence** (2 человека). Аруна — данные, радар, сайт, код. Подруга — дизайн и 7 слайдов.
> Хакатон: **NASA Space Apps Challenge 2026**, челлендж про земные аналоги Луны и Марса (**точное название взять со страницы челленджа на spaceappschallenge.org** и вписать на сайт, в слайды и сабмишн).
> **Жёсткий дедлайн сдачи: воскресенье 15 ноября 2026, 13:00 (Asia/Bishkek, UTC+6). Всё должно быть отправлено к 12:00 с запасом.**

---

## 0. Как работать с Аруной (обязательно)

1. **Говори с Аруной по-русски, просто.** Она начинающий программист. После каждого шага в 2–3 предложениях объясни, что сделал код и почему это важно для проекта. Она должна уметь объяснить жюри каждую формулу.
2. **Перед каждой задачей** коротко скажи план, потом делай. Не спрашивай разрешения на обычные шаги (установить пакет, создать файл, запустить скрипт). Спрашивай только про необратимое (удаление, force-push, публикацию).
3. **Никогда не выдумывай числа, координаты, ссылки и цитаты.** Каждое число на сайте и в статье должно приходить из файла в `data/`, который посчитал наш код. Координаты кратеров и мест — из официальных источников (IAU Gazetteer, USGS, статьи), не «по памяти».
4. **Если данные не скачиваются** — не застревай больше 20 минут. Сообщи Аруне, включи запасной вариант (см. каждую задачу) и **явно пометь** его в данных (`"source": "fallback: ..."`) и на сайте.
5. **Коммить в git после каждой готовой задачи** с понятным сообщением. Пушь в GitHub.
6. **Следи за временем.** Если задача сильно затягивается — урежь её до минимума (MVP), а не бросай проект без сайта. Приоритет: работающий сайт с реальными данными > идеальный анализ.
7. В начале каждого файла с кодом комментарий: `# Code written with assistance from Claude (Anthropic) for GroundTwin, NASA Space Apps 2026.`

## 1. Суть проекта (коротко)

**GroundTwin — Earth's ground truth for the Moon and Mars.**

Постоянную базу на Луне поставят там, где есть водяной лёд (вода, кислород, топливо). Лёд у южного полюса ищут радаром Mini-RF (LRO) по показателю **CPR** (circular polarization ratio = same-sense / opposite-sense). Проблема: высокий CPR дают и лёд, и камни — учёные спорят (Spudis et al. 2013 vs Fa et al.).
**Наш ход:** канадский спутник **RCM** (RADARSAT Constellation Mission) использует ту же гибридную компактную поляриметрию, что и Mini-RF. На Земле мы знаем, где лёд, а где камни → меряем CPR там → получаем эталон для чтения лунных карт.

Три модуля в одном сайте:
1. **Radar Twin (Луна)** — флагман. CPR на Земле (RCM) по классам «лёд / камни / гладко» + CPR, температура (Diviner) и рельеф (LOLA) в кратерах южного полюса Луны → **Ice Evidence Score**.
2. **Analog Engine (вся Земля)** — карта сходства каждой клетки Земли с целью на Луне/Марсе по физическим признакам, режимы (Наука / Операции / Строительство / Ресурсы), проверка метода (**Lift**) на известных аналогах.
3. **Mars Field Twin (Марс)** — Мангистау (Казахстан): дно исчезнувшего моря, соры, конкреции Торыш, сухость (DEM + MODIS + GPM + Sentinel-2) против кратеров Gale, Jezero и Meridiani.

Подробная теория — в `docs_internal/GroundTwin_explained.pdf` (если положили) — и в разделах ниже.

## 2. Правила Space Apps, которые нельзя нарушить

- Использование ИИ **разрешено**, но нужно честно указать где и как (поле «Use of AI» в сабмишне, README, комментарии в коде).
- Картинки/видео, созданные ИИ, — только с видимой пометкой. **Мы ИИ-картинки не используем.**
- **Никаких логотипов и символики NASA** (логотип, «meatball», флаги миссий) на сайте и в слайдах.
- Демо: **≤ 7 слайдов** (включая титульный) или видео ≤ 30 с, на английском. Хостинг демо — внешний (Google Drive/GitHub), ссылка публичная, проверить в инкогнито.
- Для глобальных наград **обязательно использовать данные NASA** (у нас: LRO Mini-RF, Diviner, LOLA, MODIS, Landsat, GPM).
- Узнаваемые имена, голоса и лица несовершеннолетних нельзя показывать в демо — уточнить у Аруны.
- Всё на сайте и в статье — **на английском**.

## 3. Структура репозитория

```
groundtwin/
  CLAUDE.md                 ← этот файл
  README.md                 ← для жюри: что это, скриншот, ссылка на сайт, данные, метод, AI use, лицензия
  LICENSE                   ← MIT
  requirements.txt
  notebooks/
    GroundTwin_01_Earth_Radar_RCM.ipynb   ← уже готов (RCM, Земля)
  pipeline/
    01_earth_radar.py       ← то же, что ноутбук 01, но скриптом
    02_moon_radar.py        ← Mini-RF + Diviner + LOLA по кратерам
    03_mangystau_field.py   ← Мангистау: DEM, MODIS, GPM, Sentinel-2 (Google Earth Engine)
    04_analog_engine.py     ← глобальная карта сходства (Google Earth Engine)
    05_validation.py        ← Lift по известным аналогам
    common.py
  data/                     ← только маленькие готовые JSON/GeoJSON/PNG (каждый < 5 МБ)
  docs/                     ← САЙТ (GitHub Pages публикует из /docs) — УЖЕ ГОТОВ
    index.html  assets/style.css  assets/app.js  assets/img/  data/*.json  paper/
  tools/make_demo_data.py   ← образец структуры всех JSON (demo)
  paper/
    groundtwin_paper.md → groundtwin_paper.pdf
  submission/
    project_page.md         ← тексты для полей сабмишна
  raw/                      ← скачанные большие файлы (в .gitignore!)
```

`.gitignore`: `raw/`, `*.tif` больше 5 МБ, `.venv/`, `__pycache__/`, `.ipynb_checkpoints/`.

## 4. Задачи по порядку (с критериями «готово»)

### T0 — Окружение (15 мин)
- Создай venv, `requirements.txt`: `numpy pandas matplotlib rasterio rioxarray pyproj shapely geopandas pystac-client requests earthengine-api geemap pillow scipy`.
- `git init`, подключи удалённый репозиторий Аруны `groundtwin` на GitHub (спроси URL), первый коммит.
- Google Earth Engine: `earthengine authenticate` (Аруна логинится в браузере) и `ee.Initialize(project='<её Cloud project id>')` — спроси project id.
- ✅ Готово, когда `python -c "import ee; ee.Initialize(project=...); print(ee.Number(1).getInfo())"` печатает 1.

### T1 — Earth Radar Twin, RCM (≤ 1 ч) — ПРИОРИТЕТ 1
- Перенеси логику из `notebooks/GroundTwin_01_Earth_Radar_RCM.ipynb` в `pipeline/01_earth_radar.py` (без Colab-специфики). Если Аруна уже запускала ноутбук в Colab и есть `earth_cpr.json` — используй его, не пересчитывай.
- Данные: STAC `https://www.eodms-sgdot.nrcan-rncan.gc.ca/search/`, коллекция `rcm-ard`, ассеты `rr`, `rl`, `local_inc_angle` (COG на S3 `rcm-ceos-ard`, без аккаунта). Документация: https://github.com/eodms-sgdot/radarsat-notebooks
- Метод: CPR = отношение **блочных средних** (5×5 пикселей) same-sense / opposite-sense; фильтр локального угла падения 30–60°; предпочтение зимним снимкам (сухой снег/мерзлота). Конвенцию каналов проверяем данными: у гладких мест CPR должен быть < 1 (если RR/RL > 1 на гладких → CPR = RL/RR). **Запиши выбранную конвенцию в JSON и в статью.**
- Сайты по классам (`ice`, `rough_rock`, `smooth`) — список в ноутбуке. **Проверь координаты** на спутниковой карте; если места нет в покрытии RCM — замени на похожее в Канаде и отметь это.
- Выход: `data/earth_cpr.json` (по сайтам и по классам: median, p25, p75, доля CPR>1, гистограмма), `data/earth_cpr_by_class.png`, `data/site_maps/*.png`.
- ✅ Готово, когда есть ≥ 1 сайт в каждом классе.

### T2 — Moon Radar Twin: Mini-RF + Diviner + LOLA (≤ 2,5 ч) — ПРИОРИТЕТ 1
- **Цели (кратеры и регионы).** 9 регионов-кандидатов Artemis III (NASA, окт. 2024): Peak near Cabeus B, Haworth, Malapert Massif, Mons Mouton Plateau, Mons Mouton, Nobile Rim 1, Nobile Rim 2, de Gerlache Rim 2, Slater Plain. Плюс полярные кратеры с вечной тенью: Shackleton, Haworth, Shoemaker, Faustini, Cabeus, de Gerlache, Sverdrup, Nobile. **Координаты и диаметры бери из IAU Gazetteer of Planetary Nomenclature** (https://planetarynames.wr.usgs.gov) — сохрани таблицу в `data/moon_targets.csv` со ссылкой на источник.
- **Mini-RF CPR:** полярная мозаика южного полюса (S-band) из PDS — продукты MOSCDR / MOSDDR (Mini-RF archive: https://pds-geosciences.wustl.edu/missions/lro/mini-rf.htm, описание: https://ode.rsl.wustl.edu/moon/ → Mini-RF). Найди точный файл мозаики CPR южного полюса (> 80° ю.ш.), скачай в `raw/`, читай rasterio. Если нужна только часть — вырежи по полярной стереографической проекции.
- **Diviner:** полярные продукты температуры (максимальная/средняя годовая температура, южный полюс) из PDS Geosciences (https://pds-geosciences.wustl.edu/missions/lro/diviner.htm).
- **LOLA:** полярный DEM южного полюса (PDS LOLA GDR polar или NASA PGDA https://pgda.gsfc.nasa.gov/products/90) → уклон и шероховатость.
- Для каждого кратера: CPR **внутри** (дно, радиус < 0.8 R) и **снаружи** (кольцо 1.2–2 R), Tmax (Diviner, внутри), медианный уклон/шероховатость (LOLA, внутри).
- **Ice Evidence Score (0–3):** +1 если CPR_in заметно выше CPR_out (порог задать и записать, напр. отношение > 1.2), +1 если дно гладкое (уклон ниже медианы по всем целям), +1 если Tmax < 110 K. Это **«совместимо со льдом»**, а не «здесь лёд».
- Сравни лунные CPR с земными классами из T1 (график: земные боксы + лунные точки). Помни: длины волн разные (RCM C ≈ 5.5 см, Mini-RF S 12.6 см) → сравниваем **порядок классов и контраст in/out**, не абсолютные числа.
- **Запасной вариант**, если мозаика Mini-RF не скачивается за 40 мин: используй значения CPR кратеров из таблиц Spudis et al. 2013 (https://ntrs.nasa.gov/api/citations/20140016845/downloads/20140016845.pdf) с пометкой `"source": "literature: Spudis et al. 2013"`. Diviner/LOLA всё равно постарайся посчитать.
- Выход: `data/moon_targets.json` (по каждой цели: координаты, CPR_in, CPR_out, Tmax, slope, IES, источник), `data/moon_vs_earth_cpr.png`, карта южного полюса с целями `data/moon_south_pole_map.png`.

### T3 — Mars Field Twin: Мангистау (≤ 1,5 ч) — ПРИОРИТЕТ 2
Идея: Мангистау (Казахстан) — дно исчезнувшего моря Тетис: слоистые осадочные породы (как в кратере Gale), соры с солями (как соляные отложения на Марсе), каменные шары-конкреции долины Торыш (форма и способ образования похожи на «черничины» Opportunity в Meridiani; размер и состав другие — говорить честно), сухо, почти нет растений, впадина Карагие ниже уровня моря.
- **Места:** долина шаров Торыш, Бозжыра, сор Тузбаир, впадина Карагие, Шеркала. Координаты НЕ выдумывать: взять из OpenStreetMap или Википедии, записать источник у каждой точки.
- **Данные (Google Earth Engine, Python API; NASA и открытые):**
  - Copernicus DEM GLO-30 (`COPERNICUS/DEM/GLO30`) — высота, уклоны, глубина Карагие;
  - MODIS LST (`MODIS/061/MOD11A2`) — перепад температуры день/ночь;
  - MODIS NDVI (`MODIS/061/MOD13A2`) — насколько нет растений;
  - GPM IMERG (`NASA/GPM_L3/IMERG_MONTHLY_V07`) — осадки;
  - Sentinel-2 SR Harmonized — безоблачная картинка в естественных цветах и индекс солей и карбонатов по SWIR (пометить «ориентировочный»).
- **Связь с T4:** посчитать, в какой процент лучших по Земле попадают клетки Мангистау в Analog Engine для mars_gale и mars_jezero (если T4 ещё не готов — сделать этот пункт после T4).
- Таблица «Мангистау ↔ Gale ↔ Meridiani» (что похоже / что нет) со ссылками: Grotzinger et al. 2014/2015 (озеро в Gale), Squyres et al. 2004 (сферулы Opportunity).
- Выход: `docs/data/mangystau.json` (`demo: false`; места: name, lat, lon, coord_source, признаки; region_stats; rank_vs_mars {mars_gale, mars_jezero}; comparison), картинки `docs/assets/img/mangystau_*.png`.
- Страница сайта `#mangystau` («Mars Field Twin: Mangystau») уже есть и читает `docs/data/mangystau.json` — менять только данные.
- Запасной вариант: если GEE не работает — значения из открытых источников с пометкой `"source"`; честно пометить.

### T4 — Analog Engine (≤ 2 ч) — ПРИОРИТЕТ 2
- GEE, сетка **0.5°** по суше (маска суши, без Антарктиды или с ней — реши и запиши).
- Признаки и источники (все NASA):
  - сухость: GPM IMERG месячные (`NASA/GPM_L3/IMERG_MONTHLY_V07`), годовая сумма осадков, среднее 2015–2024;
  - отсутствие растительности: MODIS NDVI (`MODIS/061/MOD13A2`), годовой максимум;
  - суточный перепад температур: MODIS LST (`MODIS/061/MOD11A2`) day − night, среднее;
  - холод: MODIS LST night, 5-й перцентиль;
  - пыль: MODIS AOD (`MODIS/061/MCD19A2_GRANULES`), среднее;
  - шероховатость рельефа: стандартное отклонение высоты/уклона по DEM (`USGS/GMTED2010` или `USGS/SRTMGL1_003`) внутри клетки;
  - высота: средняя высота.
- Каждый признак → **процентиль p ∈ [0,1] по всей суше** (в «экстремальную» сторону: сухо, голо, перепад, холодно, пыльно, шероховато).
- **Цели (профили t):** Moon South Pole (base), Mars Jezero, Mars Gale. Профили задаём таблицей в `pipeline/04_analog_engine.py` с объяснением каждого значения (почему такое) → в Method на сайте.
- **Сходство:** s_i = 1 − |p_i − t_i|; S = Σ w_i s_i / Σ w_i. **Режимы весов:** Science, Operations, Construction, Resources — таблица весов в коде и на сайте.
- Чтобы сайт мог переключать режимы без сервера: экспортируй **процентили признаков по каждой клетке** (GeoJSON/компактный JSON), а S считай в браузере на JS.
- Выход: `data/analog_grid.json` (клетки: lon, lat, p-признаки), `data/targets.json` (профили и веса), топ-20 мест для каждой цели/режима.

### T5 — Валидация Lift (≤ 45 мин) — ПРИОРИТЕТ 2
- Эталон: USGS «Known Terrestrial Analog Sites for Planetary Science» (https://catalog.data.gov/dataset/known-terrestrial-analog-sites-for-planetary-science) — скачай точки. Если не получается — составь список ~15 общеизвестных аналогов (Атакама, Death Valley, Haughton, Dry Valleys, Mauna Kea, Rio Tinto, MDRS Utah, Svalbard, Iceland lava fields, Devon Island, Pilbara, Danakil, Mojave, Ries crater…) **с координатами из надёжных источников** и пометкой.
- Lift = (доля эталонных мест в верхних 10% клеток) / 0.10, для каждой цели и режима. Плюс случайный бенчмарк (перемешать карту 1000 раз → p-value).
- Новые места с высоким S, которых нет в эталоне → «candidates» (особенно Центральная Азия / Казахстан).
- Выход: `data/validation.json`.

### T6 — Сайт (УЖЕ ПОСТРОЕН — подключить реальные данные) — ПРИОРИТЕТ 1
Сайт готов в `docs/` (одна страница с разделами #home #radar #explore #mangystau #method #about): `docs/index.html`, `docs/assets/style.css`, `docs/assets/app.js`. Библиотеки: Leaflet 1.9.4, Chart.js 4.4.1, KaTeX 0.16.9 (cdnjs). Сейчас в `docs/data/*.json` лежат **DEMO-данные** из `tools/make_demo_data.py` (`"demo": true` → сайт показывает жёлтый баннер DEMO и метки на графиках).
**Задача:** пайплайн T1–T5 пишет НАСТОЯЩИЕ файлы в `docs/data/` ТОЧНО в той же структуре и с `"demo": false`. Пока хоть один файл demo — баннер висит. **Сдавать с demo-данными запрещено.**

Контракты данных (смотри `tools/make_demo_data.py` как образец):
- `earth_cpr.json` — {demo, convention, look, inc_range, credit, sites:[{site, cls ∈ smooth|rough_rock|ice, lon, lat, date, scene, winter, inc_mean, n_cells, median, p25, p75, frac_gt1, hist[40]}], classes:{cls:{median,p25,p75,frac_gt1,n}}} — это ровно выход ноутбука 01.
- `moon_targets.json` — {demo, band, ratio_threshold, cold_threshold_k, slope_threshold_deg, targets:[{name, kind, lat, lon(восточная долгота, −180..180), cpr_in, cpr_out, tmax_k, slope_deg, clues:{radar,smooth,cold}, ies, source}]}. В demo координаты ПРИБЛИЗИТЕЛЬНЫЕ — заменить по IAU Gazetteer.
- `analog_grid.json` — {demo, cell_deg (0.5), features:[aridity,barren,thermal_range,cold,dust,roughness,elevation], cells:[[lon_center, lat_center, p1..p7], ...]} — p = процентили 0..1 «в экстремальную сторону».
- `targets.json` — профили целей, режимы и веса (уже заполнен командой; можно уточнять, всё видно на сайте).
- `validation.json` — {demo, top_fraction, lift:{target:{mode:value}}, p_value, known_sites:[{name,lat,lon}]}.
- `mangystau.json` — {demo, places:[{name, lat, lon, coord_source, elevation_m, slope_deg, lst_range_k, ndvi_max, precip_mm_yr, salt_index}], region_stats:{те же признаки}, rank_vs_mars:{mars_gale, mars_jezero} (= «в лучших X% клеток Земли», число 0–100), images:[{file, caption}]}; картинки — `docs/assets/img/mangystau_*.png`. Таблица «Мангистау ↔ Gale ↔ Meridiani» — текстом в `docs/index.html`.
- `moon_targets.json`: у гор (не кратеров) `ies` и `clues` = null — сайт показывает «n/a».
- Реальные T1/T2 копирует в `docs/data/` скрипт `pipeline/export_site_data.py` (из `data/*.json`).
Также: вписать имена команды, точное название челленджа и логин GitHub в раздел #about (`docs/index.html`, плейсхолдеры в квадратных скобках); поменять цвета/шрифт в `:root` в `style.css`, когда подруга даст бренд. Включить GitHub Pages: Settings → Pages → Branch `main`, folder `/docs`. Проверить сайт с телефона и в инкогнито.
✅ Готово, когда сайт открывается по `https://<login>.github.io/groundtwin/`, баннера DEMO нет, все разделы показывают реальные данные.

### T7 — Research paper (≤ 2 ч, воскресенье утром) — ПРИОРИТЕТ 2
- `paper/groundtwin_paper.md` → PDF (pandoc или HTML → PDF). 4–6 страниц, английский.
- Заголовок: *GroundTwin: Earth as a Calibration Laboratory for Lunar Radar Ice Detection and a Multi-Criteria Search for Planetary Analogs*.
- Разделы: Abstract, Introduction, Related Work (ESA CAFE, USGS analog sites, Mini-RF CPR debate, image-similarity studies), Data (таблица), Methods (T1–T5), Validation, Results (рисунки из `data/`), Limitations (длины волн, влага, чистота земного льда, отсутствие вакуума/низкой гравитации/радиации, грубая сетка, субъективные профили целей), Future Work, Data & Code Availability, **AI Use Statement**, References.
- **Каждое число — из `data/*.json`.** Каждая ссылка — реальная, проверенная (открыть URL). Нет уверенности → не писать.
- Цитаты из источников — пересказом, без длинных копий.

### T8 — README + тексты сабмишна (≤ 45 мин) — ПРИОРИТЕТ 1
- `README.md`: заголовок, слоган, скриншот сайта, ссылки (сайт, статья, демо), что делает, как запустить пайплайн, данные (NASA / CSA / ESA / прочие) с кредитами, метод кратко, ограничения, AI use, команда, лицензия.
- `submission/project_page.md` — готовые тексты на английском для полей Space Apps: Project Name, High-Level Summary (≤ ~150 слов), Project Demo link, Final Project link, Project Details (что делает, как работает, польза, что использовали), Use of Artificial Intelligence, NASA Data, Space Agency Partner Data, References.
- AI use statement (шаблон, уточнить с Аруной): *«We used Claude (Anthropic) via Claude Code and claude.ai to help write Python and HTML/JS code, debug, and edit English text. The project concept (using RCM as an Earth calibration twin for Mini-RF), site selection, data checks, interpretation of results and the visual design are our own. No AI-generated images or videos are used.»*

### T9 — Финальная проверка (воскресенье до 11:30)
- [ ] Сайт открывается в инкогнито и с телефона, все 7 страниц, нет ошибок в консоли.
- [ ] Все числа на сайте = числам в статье = числам в `data/`.
- [ ] Кредиты данных и AI statement есть на сайте, в README, в статье.
- [ ] Нет логотипов NASA. Нет ИИ-картинок.
- [ ] Репозиторий публичный, лицензия MIT, `raw/` не закоммичен.
- [ ] Ссылки на демо (7 слайдов, PDF на Google Drive/GitHub) открываются без логина.
- [ ] Сабмишн заполнен и отправлен (**Submit for Judging**) до 12:00.

## 5. Расписание (Asia/Bishkek)

| Время | Аруна + Claude Code | Подруга |
|---|---|---|
| Сб 11:00–12:00 | T0, запустить T1 (или взять результат Colab) | Бренд, цвета, шрифт → Аруне |
| Сб 12:00–15:00 | T2 Луна; параллельно каркас сайта T6 | Шаблон 7 слайдов |
| Сб 15:00–17:30 | T3 Мангистау | Тексты слайдов 1–4, 6 |
| Сб 17:30–20:30 | T4 Analog Engine + T5 Lift | Иконки/схемы для сайта, проверка сайта |
| Сб 20:30–23:30 | T6 сайт с реальными данными, деплой | Слайд 5 (результаты) |
| **Сб 23:30 — контрольная точка** | Работает ли сайт со всеми модулями? Если нет — урезать | |
| Сб 23:30 → сон до 7:00 | | |
| Вс 7:00–9:30 | T7 статья | Финал слайдов, PDF |
| Вс 9:30–11:00 | T8 README + тексты сабмишна | Проверка текстов, загрузка демо |
| Вс 11:00–11:30 | T9 проверка | Проверка |
| **Вс до 12:00** | **Submit for Judging** | |

## 6. Ключевые формулы (для кода, сайта и статьи)

- CPR = σ_SC / σ_OC (Mini-RF: SC/OC; RCM: отношение блочных средних каналов RR и RL по проверенной конвенции).
- NDVI = (NIR − Red)/(NIR + Red); NDWI = (Green − NIR)/(Green + NIR).
- s_i = 1 − |p_i − t_i|; S = Σ w_i s_i / Σ w_i.
- Lift = (доля известных аналогов в топ-10% клеток) / 0.10.
- IES = [CPR_in/CPR_out > порог] + [гладкое дно по LOLA] + [Tmax < 110 K по Diviner].

## 7. Проверенные источники (используй, проверяй ссылки)

- RCM ARD: https://registry.opendata.aws/rcm-ceos-ard/ · https://github.com/eodms-sgdot/radarsat-notebooks
- Mini-RF / LRO PDS: https://pds-geosciences.wustl.edu/missions/lro/ · Diviner: https://pds-geosciences.wustl.edu/missions/lro/diviner.htm
- Spudis et al. 2013 (CPR и лёд): https://ntrs.nasa.gov/api/citations/20140016845/downloads/20140016845.pdf
- Artemis III регионы (NASA, 2024) — проверь по nasa.gov
- IAU Gazetteer: https://planetarynames.wr.usgs.gov
- USGS Known Terrestrial Analog Sites: https://catalog.data.gov/dataset/known-terrestrial-analog-sites-for-planetary-science
- ESA CAFE (каталог аналогов): https://www.esa.int/Our_Activities/Preparing_for_the_Future/Discovery_and_Preparation/Cataloguing_otherworldly_landscapes_on_Earth
- Earthdata Search: https://search.earthdata.nasa.gov · Worldview: https://worldview.earthdata.nasa.gov
