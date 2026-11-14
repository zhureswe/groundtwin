# GroundTwin — Earth's ground truth for the Moon and Mars

NASA Space Apps Challenge 2026 · Team Code Influence

**Where does Earth *echo* like the Moon?** Lunar radar can mistake rocks for ice. GroundTwin measures the same radar signal (CPR) on Earth with Canada's RADARSAT Constellation Mission — which shares the hybrid-polarimetric design of NASA's Mini-RF — over places where we know the ground truth, and uses it to read the lunar south pole. Plus a global, explainable map of Earth analogs and Mangystau (Kazakhstan) — the floor of a vanished sea — as a Mars field twin.

- Website: https://[login].github.io/groundtwin/
- Paper: `paper/` · Demo slides: [link]

> Status: work in progress during the hackathon. While `docs/data/*.json` contain `"demo": true`, the site shows a DEMO banner.

## Modules
1. **Radar Twin (Moon)** — Earth CPR reference (RCM) + Ice Evidence Score for south-pole craters (Mini-RF radar, LOLA slopes, Diviner temperatures).
2. **Analog Engine (Earth)** — similarity of every land cell to a Moon/Mars target, by mission goal, validated on known analog sites (Lift).
3. **Mars Field Twin** — Mangystau, Kazakhstan: ancient seabed sediments, salt flats and concretions (DEM, MODIS, GPM, Sentinel-2) vs Gale, Jezero and Meridiani on Mars.

## Run
`pip install -r requirements.txt`, then `pipeline/01…05` (see `CLAUDE.md`). The site is static: open `docs/index.html` via any local server (`python -m http.server -d docs`).

## Data
NASA: LRO Mini-RF, Diviner, LOLA (PDS); MODIS, GPM IMERG, Landsat. CSA/NRCan: RADARSAT Constellation Mission CEOS-ARD. ESA: Copernicus. USGS: Known Terrestrial Analog Sites.
RADARSAT Constellation Mission Imagery © Government of Canada (2025). RADARSAT is an official mark of the Canadian Space Agency.

## Use of AI
We used Claude (Anthropic) to help write code and edit English text. The concept, data choices, checks, interpretation and design are our own. No AI-generated images or videos.

## License
MIT
