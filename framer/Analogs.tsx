import * as React from "react"
import { useEffect, useLayoutEffect, useRef, useState } from "react"
import { addPropertyControls, ControlType, RenderTarget } from "framer"

// GroundTwin analogs: a list of the top 10 (5 Moon + 5 Mars) and a detail view.
// All numbers come from the GroundTwin data files on GitHub Pages (showcase.json, explanations.json, targets.json).

const BASE = "https://zhureswe.github.io/groundtwin/"
const C = {
    s1: "#0A0E17",
    s2: "#111724",
    line: "#1B2333",
    text: "#EAF0F7",
    muted: "#8F9AAD",
    subtle: "#66718A",
    moon: "#4FD1E8",
    mars: "#FF6A3D",
}
const HEAD = "'Space Grotesk', Inter, system-ui, sans-serif"
const BODY = "Inter, system-ui, sans-serif"
const MONO = "'JetBrains Mono', ui-monospace, monospace"
const FEATS = ["aridity", "barren", "thermal_range", "cold", "dust", "roughness", "elevation"]
const FNAME: Record<string, string> = {
    aridity: "Dry",
    barren: "No plants",
    thermal_range: "Day–night swing",
    cold: "Cold",
    dust: "Dust",
    roughness: "Rough terrain",
    elevation: "High altitude",
}
const PHRASE: Record<string, string> = {
    aridity: "Drier than",
    barren: "Fewer plants than",
    thermal_range: "Larger day–night temperature swing than",
    cold: "Colder nights than",
    dust: "Dustier air than",
    roughness: "Rougher terrain than",
    elevation: "Higher ground than",
}
// From analog_grid.json "sources" (period 2015-2024).
const SOURCES: Record<string, string> = {
    aridity: "NASA GPM IMERG V07 · mean yearly precipitation",
    barren: "MODIS MOD13A2 NDVI · yearly maximum",
    thermal_range: "MODIS MOD11A2 · day minus night surface temperature",
    cold: "MODIS MOD11A2 · night surface temperature, 5th percentile",
    dust: "MODIS MOD08_M3 · aerosol optical depth 550 nm",
    roughness: "USGS GMTED2010 · terrain roughness",
    elevation: "USGS GMTED2010 · mean elevation",
}
const META: Record<string, any> = {
    moon_south_pole: {
        side: "moon",
        short: "Moon",
        head: "Moon · south pole base",
        color: C.moon,
        img: BASE + "assets/img/moon_south_pole_lroc_wac.jpg",
        credit: "Lunar south pole, LROC Wide Angle Camera mosaic · NASA/GSFC/Arizona State University",
        trek: "https://trek.nasa.gov/moon/",
        trekName: "NASA Moon Trek",
    },
    mars_gale: {
        side: "mars",
        short: "Mars",
        head: "Mars · Gale crater",
        color: C.mars,
        img: "https://commons.wikimedia.org/wiki/Special:FilePath/Gale_crater_with_Curiosity_landing_ellipse_(PIA15687).jpg?width=900",
        credit: "Gale crater and Mount Sharp, PIA15687 · NASA/JPL-Caltech/ESA/DLR/FU Berlin/MSSS",
        trek: "https://trek.nasa.gov/mars/",
        trekName: "NASA Mars Trek",
    },
}
const metaFor = (t: string) => META[t] || (t && t.indexOf("mars") === 0 ? META.mars_gale : META.moon_south_pole)

// ---------- data ----------
let cache: Promise<any> | null = null
function loadAll() {
    if (!cache) {
        const get = (n: string) =>
            fetch(BASE + "data/" + n + ".json").then((r) => {
                if (!r.ok) throw new Error(n + ".json HTTP " + r.status)
                return r.json()
            })
        cache = Promise.all([get("showcase"), get("explanations"), get("targets"), get("famous_analogs").catch(() => ({ sites: [] }))]).then(([sc, ex, tg, fa]) => build(sc, ex, tg, fa))
        cache.catch(() => {
            cache = null
        })
    }
    return cache
}
function row(e: any, fallback: any = {}) {
    return {
        place: e.place || fallback.region,
        S: typeof e.S === "number" ? e.S : fallback.S,
        position: e.position,
        nCells: e.n_cells,
        topPercent: e.top_percent,
        features: e.features || {},
        profile: e.profile || {},
        match: e.match_features || fallback.matches || [],
        partly: e.partly_features || [],
        differ: e.differ_features || fallback.differs || [],
        textMatch: e.matches || "",
        textDiffer: e.differs || "",
    }
}
function build(sc: any, ex: any, tg: any, fa: any) {
    const items: any[] = []
    const keys = ["moon_south_pole", sc.mars_target || "mars_gale"]
    for (const key of keys) {
        const tops = ((sc.top || {})[key] || []).slice(0, 5)
        const exs = (ex.top || {})[key] || []
        tops.forEach((t: any, i: number) => {
            const r: any = row(exs[i] || {}, t)
            r.profile = Object.keys(r.profile).length ? r.profile : ((tg.targets || {})[key] || {}).profile || {}
            items.push({ ...r, id: metaFor(key).side + "-" + (i + 1), kind: "top", target: key, listRank: i + 1, region: t.region, lat: t.lat, lon: t.lon })
        })
    }
    const bench: any[] = []
    for (const card of sc.cards || []) {
        const ers = (ex.cards || {})[card.key] || []
        const id = card.key === "moon_reference" ? "moon-ref" : card.key === "mars_reference" ? "mars-ref" : card.key
        const name = String(card.title || "").split(": ").slice(1).join(": ") || card.title
        bench.push({ id, kind: "bench", key: card.key, title: card.title, name, target: card.target, sites: card.sites || [], facts: card.facts || [], notLike: card.not_like || [], rows: ers.map((e: any) => row(e)) })
    }
    const famous: any[] = (fa.sites || []).map((f: any, i: number) => {
        const tt = (f.targets || {})[f.primary] || {}
        const r: any = f.scored
            ? { place: f.name, S: tt.S, position: tt.position, nCells: tt.n_cells, topPercent: tt.top_percent, features: f.features || {}, profile: tt.profile || {}, match: tt.match || [], partly: tt.partly || [], differ: tt.differ || [], textMatch: "", textDiffer: "" }
            : { place: f.name, features: {}, profile: {}, match: [], partly: [], differ: [] }
        return { ...r, id: f.id === "mangystau" ? "mangystau" : "f-" + f.id, kind: "famous", famous: f, listRank: i + 1, target: f.primary, region: f.name + ", " + f.country, lat: f.lat, lon: f.lon, scored: !!f.scored }
    })
    return { famous, items, bench, targets: tg.targets || {}, nCells: sc.n_cells || 60215, weights: ((tg.modes || {}).science || {}).weights || {}, aiLabel: ex.label || "AI-written from our data" }
}

// ---------- helpers ----------
const cosd = (d: number) => Math.cos((d * Math.PI) / 180)
const fmtLL = (lat: number, lon: number) => Math.abs(lat).toFixed(2) + "°" + (lat >= 0 ? "N" : "S") + ", " + Math.abs(lon).toFixed(2) + "°" + (lon >= 0 ? "E" : "W")
const fmtPct = (p: number) => (typeof p !== "number" ? "–" : p < 0.1 ? p.toFixed(3) : p.toFixed(1))
const fmtInt = (n: number) => (typeof n === "number" ? n.toLocaleString("en-US") : "–")
function box(lat: number, lon: number, dLat: number) {
    const dLon = dLat / Math.max(0.2, cosd(lat))
    return { w: lon - dLon / 2, s: lat - dLat / 2, e: lon + dLon / 2, n: lat + dLat / 2 }
}
function s2Url(lat: number, lon: number, dLat: number, px: number) {
    const b = box(lat, lon, dLat)
    return "https://tiles.maps.eox.at/wms?service=WMS&request=GetMap&version=1.1.1&layers=s2cloudless-2023&styles=&srs=EPSG:4326&bbox=" + [b.w, b.s, b.e, b.n].map((v) => v.toFixed(4)).join(",") + "&width=" + px + "&height=" + px + "&format=image/jpeg"
}
function reliefUrl(lat: number, lon: number, dLat: number, px: number) {
    const b = box(lat, lon, dLat)
    return "https://wvs.earthdata.nasa.gov/api/v1/snapshot?REQUEST=GetSnapshot&BBOX=" + [b.s, b.w, b.n, b.e].map((v) => v.toFixed(4)).join(",") + "&CRS=EPSG:4326&LAYERS=ASTER_GDEM_Color_Shaded_Relief&FORMAT=image/jpeg&WIDTH=" + px + "&HEIGHT=" + px
}
const earthUrl = (lat: number, lon: number) => "https://earth.google.com/web/@" + lat + "," + lon + ",800a,60000d,35y,0h,0t,0r"
const worldviewUrl = (lat: number, lon: number) => {
    const b = box(lat, lon, 3)
    return "https://worldview.earthdata.nasa.gov/?v=" + [b.w, b.s, b.e, b.n].map((v) => v.toFixed(2)).join(",")
}
const status = (r: any, f: string) => (r.match.indexOf(f) >= 0 ? "match" : r.differ.indexOf(f) >= 0 ? "differs" : r.partly.indexOf(f) >= 0 ? "partly" : "partly")

function useWidth(ref: React.RefObject<HTMLDivElement>) {
    const [w, setW] = useState(1200)
    useEffect(() => {
        const el = ref.current
        if (!el || typeof ResizeObserver === "undefined") return
        const ro = new ResizeObserver((es) => setW(Math.round(es[0].contentRect.width)))
        ro.observe(el)
        setW(el.getBoundingClientRect().width || 1200)
        return () => ro.disconnect()
    }, [])
    return w
}
// On the live site, let the page grow with the content instead of a fixed page height.
function useAutoPageHeight(ref: React.RefObject<HTMLDivElement>, dep: any) {
    const iso = typeof window !== "undefined" ? useLayoutEffect : useEffect
    iso(() => {
        if (RenderTarget.current() === RenderTarget.canvas) return
        let el: HTMLElement | null = ref.current ? ref.current.parentElement : null
        for (let i = 0; el && i < 10; i++) {
            if (el.querySelector("footer") || el.querySelector("nav")) break
            el.style.height = "auto"
            el.style.minHeight = "0"
            el = el.parentElement
        }
    }, [dep])
}

// ---------- small pieces ----------
function Chip({ color, children }: any) {
    return (
        <span style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "5px 11px", borderRadius: 999, border: "1px solid " + color + "55", background: color + "14", color, fontFamily: MONO, fontSize: 11, letterSpacing: "0.04em", textTransform: "uppercase", whiteSpace: "nowrap" }}>
            <span style={{ width: 6, height: 6, borderRadius: 3, background: color }} />
            {children}
        </span>
    )
}
function MiniBars({ r, color }: any) {
    return (
        <div style={{ display: "flex", alignItems: "flex-end", gap: 3, height: 16, marginTop: 8 }} aria-hidden>
            {FEATS.map((f) => {
                const st = status(r, f)
                const p = Math.max(0.12, Math.min(1, r.features[f] || 0))
                return <span key={f} title={FNAME[f] + ": " + st} style={{ width: 7, height: Math.round(p * 16), borderRadius: 2, background: st === "differs" ? C.subtle : color, opacity: st === "match" ? 1 : st === "partly" ? 0.4 : 0.6 }} />
            })}
        </div>
    )
}
function Card({ it, href }: any) {
    const m = metaFor(it.target)
    const [hov, setHov] = useState(false)
    return (
        <a
            href={href}
            onMouseEnter={() => setHov(true)}
            onMouseLeave={() => setHov(false)}
            style={{ display: "grid", gridTemplateColumns: "64px minmax(0,1fr) auto", gap: 14, alignItems: "center", padding: "12px 16px 12px 12px", borderRadius: 14, border: "1px solid " + (hov ? m.color + "aa" : C.line), background: hov ? C.s2 : C.s1, textDecoration: "none", color: C.text, transition: "border-color .2s, background .2s, transform .2s", transform: hov ? "translateY(-2px)" : "none" }}
        >
            <div style={{ width: 64, height: 64, borderRadius: 10, overflow: "hidden", background: C.s2, position: "relative" }}>
                <img src={s2Url(it.lat, it.lon, 0.5, 160)} alt={"Sentinel-2 view of " + it.region} loading="lazy" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
                <span style={{ position: "absolute", left: 6, top: 4, fontFamily: MONO, fontSize: 11, fontWeight: 700, color: "#fff", textShadow: "0 1px 3px rgba(0,0,0,.9)" }}>{"#" + it.listRank}</span>
            </div>
            <div style={{ minWidth: 0 }}>
                <div style={{ fontFamily: HEAD, fontSize: 17, fontWeight: 600, lineHeight: 1.25, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{it.region}</div>
                <div style={{ fontFamily: MONO, fontSize: 11, color: C.subtle, marginTop: 3, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {it.kind === "famous" ? it.famous.tag + (it.scored ? " · top " + fmtPct(it.topPercent) + "%" : "") : fmtLL(it.lat, it.lon) + " · top " + fmtPct(it.topPercent) + "% of land"}
                </div>
                {it.scored === false ? <div style={{ fontSize: 12, color: C.subtle, marginTop: 8 }}>Not scored: {it.famous.reason}</div> : <MiniBars r={it} color={m.color} />}
            </div>
            <div style={{ textAlign: "right" }}>
                <div style={{ fontFamily: HEAD, fontSize: 28, fontWeight: 700, color: it.scored === false ? C.subtle : m.color, lineHeight: 1 }}>{typeof it.S === "number" ? it.S.toFixed(2) : "–"}</div>
                <div style={{ fontFamily: MONO, fontSize: 10, color: C.subtle, marginTop: 5 }}>{hov ? "details →" : it.kind === "famous" && it.scored ? "vs " + m.short : "score"}</div>
            </div>
        </a>
    )
}
function Loading({ err }: any) {
    return <div style={{ padding: 28, color: C.muted, fontFamily: MONO, fontSize: 12 }}>{err ? "Could not load the data: " + err : "Loading the analogs…"}</div>
}

// ---------- list ----------
/**
 * @framerSupportedLayoutWidth fixed
 * @framerSupportedLayoutHeight any-prefer-fixed
 * @framerIntrinsicWidth 1200
 * @framerIntrinsicHeight 900
 */
export function AnalogList(props: any) {
    const ref = useRef<HTMLDivElement>(null)
    const w = useWidth(ref)
    const [d, setD] = useState<any>(null)
    const [err, setErr] = useState("")
    useEffect(() => {
        loadAll().then(setD).catch((e) => setErr(String(e && e.message ? e.message : e)))
    }, [])
    useAutoPageHeight(ref, d)
    const path = props.detailPath || "/analog"
    const two = w > 780
    const [tab, setTab] = useState<string>("famous")
    const tabBtn = (key: string, label: string, sub: string) => (
        <button
            key={key}
            onClick={() => setTab(key)}
            style={{ cursor: "pointer", textAlign: "left", padding: "12px 18px", borderRadius: 14, border: "1px solid " + (tab === key ? C.moon + "88" : C.line), background: tab === key ? C.s2 : "transparent", color: tab === key ? C.text : C.muted, fontFamily: BODY }}
        >
            <div style={{ fontFamily: HEAD, fontSize: 16, fontWeight: 600 }}>{label}</div>
            <div style={{ fontFamily: MONO, fontSize: 10.5, color: C.subtle, marginTop: 3 }}>{sub}</div>
        </button>
    )
    const famous = d ? d.famous : []
    return (
        <div ref={ref} style={{ width: "100%", color: C.text, fontFamily: BODY, ...props.style }}>
            {!d ? (
                <Loading err={err} />
            ) : (
                <>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 26 }}>
                        {famous.length ? tabBtn("famous", "Famous field analogs", "10 places agencies use · our score") : null}
                        {tabBtn("formula", "Our formula's top 10", "5 for the Moon + 5 for Mars")}
                    </div>
                    {tab === "famous" && famous.length ? (
                        <>
                            <div style={{ display: "grid", gridTemplateColumns: two ? "1fr 1fr" : "1fr", gap: 10 }}>
                                {famous.map((it: any) => (
                                    <Card key={it.id} it={it} href={path + "?id=" + it.id} />
                                ))}
                            </div>
                            <p style={{ margin: "22px 0 0", fontSize: 13, lineHeight: 1.55, color: C.muted, maxWidth: 820 }}>
                                Well-known places where space agencies test rovers, suits and crews, each scored with our formula on its own 0.5° cell (score S from 0 to 1, rank among {fmtInt(d.nCells)} land cells). Many were picked for geology, chemistry or logistics, which our 7 climate and terrain criteria do not measure, so some rank low.
                            </p>
                        </>
                    ) : (
                        <>
                            <div style={{ display: "grid", gridTemplateColumns: two ? "1fr 1fr" : "1fr", gap: two ? 28 : 36 }}>
                                {["moon", "mars"].map((side) => {
                                    const list = d.items.filter((x: any) => metaFor(x.target).side === side)
                                    if (!list.length) return null
                                    const m = metaFor(list[0].target)
                                    const label = ((d.targets[list[0].target] || {}).label || m.head).replace(" - ", " · ")
                                    return (
                                        <div key={side}>
                                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 14 }}>
                                                <Chip color={m.color}>{label}</Chip>
                                                <span style={{ fontFamily: MONO, fontSize: 11, color: C.subtle }}>top 5</span>
                                            </div>
                                            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                                                {list.map((it: any) => (
                                                    <Card key={it.id} it={it} href={path + "?id=" + it.id} />
                                                ))}
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                            <p style={{ margin: "22px 0 0", fontSize: 13, lineHeight: 1.55, color: C.muted, maxWidth: 820 }}>
                                The best-scoring 0.5° cells on Earth, at least 600 km apart, chosen by the score alone. Several fall in Xinjiang: the Tarim Basin and the Kunlun foothills are among the driest, barest high places on Earth. Names are provinces (FAO GAUL level 1), so cells far apart can share a name; the coordinates tell them apart.
                            </p>
                            {d.bench.length ? (
                                <div style={{ marginTop: 22, paddingTop: 18, borderTop: "1px solid " + C.line, display: "flex", flexWrap: "wrap", gap: "10px 22px", alignItems: "baseline" }}>
                                    <span style={{ fontFamily: MONO, fontSize: 11, color: C.subtle, textTransform: "uppercase", letterSpacing: "0.06em" }}>For comparison · not in the top 10</span>
                                    {d.bench.map((b: any) => (
                                        <a key={b.id} href={path + "?id=" + b.id} style={{ color: C.text, textDecoration: "none", fontSize: 14, borderBottom: "1px solid " + C.line, paddingBottom: 2 }}>
                                            {b.name} <span style={{ color: C.subtle, fontFamily: MONO, fontSize: 11 }}>{b.rows[0] ? "top " + fmtPct(b.rows[0].topPercent) + "%" : ""}</span> →
                                        </a>
                                    ))}
                                </div>
                            ) : null}
                        </>
                    )}
                </>
            )}
        </div>
    )
}
addPropertyControls(AnalogList, {
    detailPath: { type: ControlType.String, title: "Detail page", defaultValue: "/analog" },
})

// ---------- detail ----------
function Section({ title, kicker, children, mt = 56 }: any) {
    return (
        <section style={{ marginTop: mt }}>
            {kicker ? <div style={{ fontFamily: MONO, fontSize: 11, color: C.subtle, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>{kicker}</div> : null}
            {title ? <h2 style={{ fontFamily: HEAD, fontSize: 26, fontWeight: 700, margin: "0 0 18px", letterSpacing: "-0.01em" }}>{title}</h2> : null}
            {children}
        </section>
    )
}
function Shot({ src, title, credit, rect, alt }: any) {
    return (
        <figure style={{ margin: 0 }}>
            <div style={{ position: "relative", aspectRatio: "1 / 1", borderRadius: 14, overflow: "hidden", background: C.s2, border: "1px solid " + C.line }}>
                <img src={src} alt={alt} loading="lazy" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
                {rect ? <span style={{ position: "absolute", left: (50 - rect.w / 2) + "%", top: (50 - rect.h / 2) + "%", width: rect.w + "%", height: rect.h + "%", border: "1.5px solid #fff", boxShadow: "0 0 0 1px rgba(0,0,0,.5)", borderRadius: 2 }} /> : null}
            </div>
            <figcaption style={{ marginTop: 10 }}>
                <div style={{ fontSize: 14, fontWeight: 600 }}>{title}</div>
                <div style={{ fontFamily: MONO, fontSize: 10.5, color: C.subtle, marginTop: 3, lineHeight: 1.5 }}>{credit}</div>
            </figcaption>
        </figure>
    )
}
const S2_CREDIT = "Sentinel-2 cloudless 2023 by EOX · contains modified Copernicus Sentinel data"
const RELIEF_CREDIT = "NASA/METI ASTER GDEM shaded relief · via NASA GIBS"
function Images({ lat, lon, cols }: any) {
    const c = cosd(lat)
    const wide = 4
    const km = (deg: number) => Math.round((deg * 111) / 10) * 10
    return (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(" + cols + ", minmax(0,1fr))", gap: 18 }}>
            <Shot src={s2Url(lat, lon, 0.5, 720)} alt="Sentinel-2 close-up of the scored cell" title={"Close-up · about " + Math.round(0.5 * 111) + " km across"} credit={S2_CREDIT} rect={{ w: c * 100 - 1, h: 99 }} />
            <Shot src={s2Url(lat, lon, wide, 720)} alt="Sentinel-2 view of the region" title={"Region · about " + km(wide) + " km across"} credit={S2_CREDIT} rect={{ w: (0.5 / wide) * 100 * c, h: (0.5 / wide) * 100 }} />
            <Shot src={reliefUrl(lat, lon, wide, 720)} alt="Terrain relief of the region" title="Terrain relief · same area" credit={RELIEF_CREDIT} rect={{ w: (0.5 / wide) * 100 * c, h: (0.5 / wide) * 100 }} />
        </div>
    )
}
function Criteria({ r, color, weights, wide }: any) {
    return (
        <div style={{ borderTop: "1px solid " + C.line }}>
            {FEATS.map((f) => {
                const p = typeof r.features[f] === "number" ? r.features[f] : null
                const t = typeof r.profile[f] === "number" ? r.profile[f] : null
                const st = status(r, f)
                const stColor = st === "match" ? color : st === "partly" ? C.muted : C.subtle
                return (
                    <div key={f} style={{ display: "grid", gridTemplateColumns: wide ? "150px minmax(0,1fr) 84px" : "minmax(0,1fr) auto", gap: wide ? 18 : 10, alignItems: "center", padding: "14px 0", borderBottom: "1px solid " + C.line }}>
                        <div>
                            <div style={{ fontSize: 15, fontWeight: 600 }}>{FNAME[f]}</div>
                            <div style={{ fontFamily: MONO, fontSize: 10.5, color: C.subtle, marginTop: 2 }}>weight ×{weights[f] ?? "–"}</div>
                        </div>
                        {wide ? null : <StatusTag st={st} c={stColor} />}
                        <div style={{ gridColumn: wide ? "auto" : "1 / -1" }}>
                            <div style={{ position: "relative", height: 8, borderRadius: 4, background: C.s2 }}>
                                {p !== null ? <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: p * 100 + "%", borderRadius: 4, background: color, opacity: st === "match" ? 1 : 0.45 }} /> : null}
                                {t !== null ? <div title="target" style={{ position: "absolute", left: "calc(" + t * 100 + "% - 1px)", top: -5, width: 2, height: 18, background: "#fff", borderRadius: 1 }} /> : null}
                            </div>
                            <div style={{ fontSize: 13, color: C.muted, marginTop: 8, lineHeight: 1.45 }}>
                                {p !== null ? PHRASE[f] + " " + Math.round(p * 100) + "% of Earth's land" : "No value"}
                                {t !== null ? <span style={{ color: C.subtle }}> · target {t.toFixed(2)}</span> : null}
                            </div>
                            <div style={{ fontFamily: MONO, fontSize: 10.5, color: C.subtle, marginTop: 3 }}>{SOURCES[f]}</div>
                        </div>
                        {wide ? <StatusTag st={st} c={stColor} /> : null}
                    </div>
                )
            })}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 16, marginTop: 12, fontFamily: MONO, fontSize: 10.5, color: C.subtle }}>
                <span><span style={{ display: "inline-block", width: 14, height: 6, borderRadius: 3, background: color, verticalAlign: "middle", marginRight: 6 }} />place, percentile among Earth's land</span>
                <span><span style={{ display: "inline-block", width: 2, height: 12, background: "#fff", verticalAlign: "middle", marginRight: 6 }} />target profile</span>
            </div>
        </div>
    )
}
function StatusTag({ st, c }: any) {
    const label = st === "match" ? "Match" : st === "partly" ? "Partly" : "Differs"
    return <span style={{ justifySelf: "end", fontFamily: MONO, fontSize: 11, color: c, border: "1px solid " + c + "66", borderRadius: 999, padding: "3px 10px", whiteSpace: "nowrap" }}>{label}</span>
}
function Stat({ label, value, sub }: any) {
    return (
        <div>
            <div style={{ fontFamily: MONO, fontSize: 10.5, color: C.subtle, textTransform: "uppercase", letterSpacing: "0.05em" }}>{label}</div>
            <div style={{ fontFamily: HEAD, fontSize: 20, fontWeight: 600, marginTop: 4 }}>{value}</div>
            {sub ? <div style={{ fontSize: 12, color: C.muted, marginTop: 2 }}>{sub}</div> : null}
        </div>
    )
}
function ScoreCard({ r, color, nCells }: any) {
    return (
        <div style={{ padding: 24, borderRadius: 18, border: "1px solid " + C.line, background: C.s1 }}>
            <div style={{ fontFamily: MONO, fontSize: 11, color: C.subtle, textTransform: "uppercase", letterSpacing: "0.06em" }}>Our score</div>
            <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginTop: 6 }}>
                <span style={{ fontFamily: HEAD, fontSize: 64, fontWeight: 700, color, lineHeight: 1 }}>{typeof r.S === "number" ? r.S.toFixed(2) : "–"}</span>
                <span style={{ color: C.muted, fontSize: 14 }}>of 1.00</span>
            </div>
            <div style={{ fontSize: 13, color: C.muted, marginTop: 8, lineHeight: 1.5 }}>S = 1 means a perfect match on all 7 criteria (Science-mode weights).</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 18, paddingTop: 16, borderTop: "1px solid " + C.line }}>
                <Stat label="Rank" value={"#" + fmtInt(r.position)} sub={"of " + fmtInt(r.nCells || nCells) + " land cells"} />
                <Stat label="Share" value={"top " + fmtPct(r.topPercent) + "%"} sub="of Earth's land" />
            </div>
        </div>
    )
}
function TargetPanel({ target, d }: any) {
    const m = metaFor(target)
    const tg = d.targets[target] || {}
    return (
        <div style={{ borderRadius: 18, border: "1px solid " + C.line, background: C.s1, overflow: "hidden" }}>
            <div style={{ aspectRatio: "4 / 3", background: C.s2 }}>
                <img src={m.img} alt={tg.label || m.head} loading="lazy" style={{ width: "100%", height: "100%", objectFit: "cover", display: "block" }} />
            </div>
            <div style={{ padding: 20 }}>
                <div style={{ fontFamily: MONO, fontSize: 10.5, color: C.subtle, lineHeight: 1.5 }}>{m.credit}</div>
                <div style={{ fontFamily: HEAD, fontSize: 19, fontWeight: 600, marginTop: 12 }}>{(tg.label || m.head).replace(" - ", " · ")}</div>
                <div style={{ fontSize: 13, color: C.muted, marginTop: 6, lineHeight: 1.5 }}>The white marks on the bars are this target's profile on the same 7 criteria.</div>
                {tg.cannot && tg.cannot.length ? (
                    <>
                        <div style={{ fontFamily: MONO, fontSize: 10.5, color: C.subtle, textTransform: "uppercase", letterSpacing: "0.05em", marginTop: 18 }}>What Earth cannot reproduce</div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 8 }}>
                            {tg.cannot.map((x: string) => (
                                <span key={x} style={{ fontSize: 12.5, color: C.text, background: C.s2, border: "1px solid " + C.line, borderRadius: 8, padding: "4px 9px" }}>{x}</span>
                            ))}
                        </div>
                    </>
                ) : null}
            </div>
        </div>
    )
}
function LinkBtn({ href, children }: any) {
    return (
        <a href={href} target="_blank" rel="noopener" style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "11px 16px", borderRadius: 12, border: "1px solid " + C.line, background: C.s1, color: C.text, textDecoration: "none", fontSize: 14 }}>
            {children} <span style={{ color: C.subtle }}>↗</span>
        </a>
    )
}
function plain(r: any) {
    const a = r.textMatch || ""
    const b = (r.textDiffer || "").split(" Earth cannot reproduce")[0]
    return (a + " " + b).trim()
}
function NavRow({ prev, next, path, listPath }: any) {
    const a = { color: C.muted, textDecoration: "none", fontSize: 14 }
    return (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <a href={listPath} style={{ ...a, color: C.text }}>← All analogs</a>
            {prev || next ? (
                <div style={{ display: "flex", gap: 18 }}>
                    {prev ? <a href={path + "?id=" + prev.id} style={a}>← {prev.short}</a> : null}
                    {next ? <a href={path + "?id=" + next.id} style={a}>{next.short} →</a> : null}
                </div>
            ) : null}
        </div>
    )
}

/**
 * @framerSupportedLayoutWidth fixed
 * @framerSupportedLayoutHeight any-prefer-fixed
 * @framerIntrinsicWidth 1200
 * @framerIntrinsicHeight 2400
 */
export default function AnalogDetail(props: any) {
    const ref = useRef<HTMLDivElement>(null)
    const w = useWidth(ref)
    const [d, setD] = useState<any>(null)
    const [err, setErr] = useState("")
    const [id, setId] = useState<string>(props.previewId || "moon-1")
    useEffect(() => {
        try {
            const q = new URLSearchParams(window.location.search).get("id")
            if (q && RenderTarget.current() !== RenderTarget.canvas) setId(q)
        } catch (e) {}
        loadAll().then(setD).catch((e) => setErr(String(e && e.message ? e.message : e)))
    }, [])
    const all = d ? d.items.concat(d.bench, d.famous || []) : []
    const it = d ? all.find((x: any) => x.id === id) || d.items[0] : null
    useEffect(() => {
        if (it && RenderTarget.current() !== RenderTarget.canvas) document.title = (it.region || it.name) + " — GroundTwin analog"
    }, [it && it.id])
    useAutoPageHeight(ref, it && it.id)
    const path = props.detailPath || "/analog"
    const listPath = props.listPath || "/analogs"
    const wide = w > 860
    const mid = w > 560
    if (!it) return <div ref={ref} style={{ width: "100%", ...props.style }}><Loading err={err} /></div>
    const m = metaFor(it.target)
    const targetLabel = ((d.targets[it.target] || {}).label || m.head).replace(" - ", " · ")

    if (it.kind === "famous") {
        const list = d.famous
        const idx = list.indexOf(it)
        const prevIt = list[(idx - 1 + list.length) % list.length]
        const nextIt = list[(idx + 1) % list.length]
        const f = it.famous
        const other = Object.keys(f.targets || {}).filter((t) => t !== f.primary)
        const tcard = (t: string) => {
            const v = f.targets[t]
            return { S: v.S, position: v.position, nCells: v.n_cells, topPercent: v.top_percent }
        }
        return (
            <div ref={ref} style={{ width: "100%", color: C.text, fontFamily: BODY, ...props.style }}>
                <NavRow prev={{ id: prevIt.id, short: prevIt.famous.name }} next={{ id: nextIt.id, short: nextIt.famous.name }} path={path} listPath={listPath} />
                <div style={{ marginTop: 36 }}>
                    <Chip color={m.color}>{"Famous field analog · " + f.tag}</Chip>
                    <h1 style={{ fontFamily: HEAD, fontSize: wide ? 56 : mid ? 42 : 34, fontWeight: 700, lineHeight: 1.05, letterSpacing: "-0.02em", margin: "18px 0 0" }}>{f.name}</h1>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px 22px", marginTop: 16, fontFamily: MONO, fontSize: 12, color: C.muted }}>
                        <span>{f.country}</span>
                        <span>{fmtLL(f.lat, f.lon)}</span>
                        <span>coordinates: {f.coord_source}</span>
                    </div>
                    <p style={{ fontSize: 17, lineHeight: 1.6, color: C.muted, margin: "20px 0 0", maxWidth: 820 }}>{f.blurb}</p>
                </div>
                {it.scored ? (
                    <div style={{ display: "grid", gridTemplateColumns: mid ? "1fr 1fr" : "1fr", gap: 18, marginTop: 36 }}>
                        {[f.primary].concat(other).map((t: string) => (
                            <div key={t}>
                                <div style={{ fontFamily: MONO, fontSize: 11, color: metaFor(t).color, textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 10 }}>{"vs " + ((d.targets[t] || {}).label || metaFor(t).head).replace(" - ", " · ")}</div>
                                <ScoreCard r={tcard(t)} color={metaFor(t).color} nCells={d.nCells} />
                            </div>
                        ))}
                    </div>
                ) : (
                    <div style={{ marginTop: 36, padding: 22, borderRadius: 16, border: "1px solid " + C.line, background: C.s1, maxWidth: 820 }}>
                        <div style={{ fontFamily: MONO, fontSize: 11, color: C.subtle, textTransform: "uppercase", letterSpacing: "0.06em" }}>Not scored</div>
                        <div style={{ fontSize: 15, color: C.muted, marginTop: 8, lineHeight: 1.6 }}>We could not score this place with our formula: {f.reason}. The satellite views below still show what it looks like.</div>
                    </div>
                )}
                <Section kicker="Satellite view" title="What the place looks like" mt={52}>
                    <Images lat={f.lat} lon={f.lon} cols={wide ? 3 : mid ? 2 : 1} />
                    {it.scored ? <div style={{ fontSize: 13, color: C.muted, marginTop: 14 }}>The white box is the 0.5° cell we scored.</div> : null}
                </Section>
                {it.scored ? (
                    <div style={{ display: "grid", gridTemplateColumns: wide ? "minmax(0,1.45fr) minmax(0,1fr)" : "1fr", gap: 36, marginTop: 56, alignItems: "start" }}>
                        <Section kicker="7 criteria · NASA / USGS data, 2015–2024" title={"How it compares with " + m.short} mt={0}>
                            <Criteria r={it} color={m.color} weights={d.weights} wide={mid} />
                        </Section>
                        <Section kicker="Target" title="Compared with" mt={0}>
                            <TargetPanel target={it.target} d={d} />
                        </Section>
                    </div>
                ) : null}
                <Section kicker="Explore" title="See it yourself">
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                        <LinkBtn href={earthUrl(f.lat, f.lon)}>Open in Google Earth</LinkBtn>
                        <LinkBtn href={worldviewUrl(f.lat, f.lon)}>NASA Worldview</LinkBtn>
                        <LinkBtn href={m.trek}>{m.trekName}</LinkBtn>
                    </div>
                </Section>
                <Section kicker="More field analogs" title="Keep exploring">
                    <div style={{ display: "grid", gridTemplateColumns: mid ? "1fr 1fr" : "1fr", gap: 10 }}>
                        <Card it={prevIt} href={path + "?id=" + prevIt.id} />
                        <Card it={nextIt} href={path + "?id=" + nextIt.id} />
                    </div>
                </Section>
            </div>
        )
    }

    if (it.kind === "top") {
        const idx = d.items.indexOf(it)
        const prevIt = d.items[(idx - 1 + d.items.length) % d.items.length]
        const nextIt = d.items[(idx + 1) % d.items.length]
        const nm = (x: any) => ({ id: x.id, short: metaFor(x.target).short + " #" + x.listRank })
        const kmEW = Math.round(55.6 * cosd(it.lat))
        return (
            <div ref={ref} style={{ width: "100%", color: C.text, fontFamily: BODY, ...props.style }}>
                <NavRow prev={nm(prevIt)} next={nm(nextIt)} path={path} listPath={listPath} />
                <div style={{ display: "grid", gridTemplateColumns: wide ? "minmax(0,1.5fr) minmax(0,1fr)" : "1fr", gap: 28, marginTop: 36, alignItems: "end" }}>
                    <div>
                        <Chip color={m.color}>{targetLabel + " · #" + it.listRank + " of 5"}</Chip>
                        <h1 style={{ fontFamily: HEAD, fontSize: wide ? 56 : mid ? 42 : 34, fontWeight: 700, lineHeight: 1.05, letterSpacing: "-0.02em", margin: "18px 0 0" }}>{it.region}</h1>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: "8px 22px", marginTop: 16, fontFamily: MONO, fontSize: 12, color: C.muted }}>
                            <span>{fmtLL(it.lat, it.lon)}</span>
                            <span>0.5° grid cell · about 56 × {kmEW} km</span>
                            <span>Earth twin of {m.short}</span>
                        </div>
                    </div>
                    <ScoreCard r={it} color={m.color} nCells={d.nCells} />
                </div>

                <Section kicker="Satellite view" title="What the place looks like" mt={52}>
                    <Images lat={it.lat} lon={it.lon} cols={wide ? 3 : mid ? 2 : 1} />
                    <div style={{ fontSize: 13, color: C.muted, marginTop: 14 }}>The white box is the 0.5° cell we scored.</div>
                </Section>

                <div style={{ display: "grid", gridTemplateColumns: wide ? "minmax(0,1.45fr) minmax(0,1fr)" : "1fr", gap: 36, marginTop: 56, alignItems: "start" }}>
                    <Section kicker="7 criteria · NASA / USGS data, 2015–2024" title="How it compares" mt={0}>
                        <Criteria r={it} color={m.color} weights={d.weights} wide={mid} />
                    </Section>
                    <Section kicker="Target" title="Compared with" mt={0}>
                        <TargetPanel target={it.target} d={d} />
                    </Section>
                </div>

                {plain(it) ? (
                    <Section kicker={d.aiLabel} title="In plain words">
                        <p style={{ fontSize: 15.5, lineHeight: 1.65, color: C.muted, margin: 0, maxWidth: 860 }}>{plain(it)}</p>
                    </Section>
                ) : null}

                <Section kicker="Explore" title="See it yourself">
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
                        <LinkBtn href={earthUrl(it.lat, it.lon)}>Open in Google Earth</LinkBtn>
                        <LinkBtn href={worldviewUrl(it.lat, it.lon)}>NASA Worldview</LinkBtn>
                        <LinkBtn href={m.trek}>{m.trekName}</LinkBtn>
                    </div>
                </Section>

                <Section kicker="More analogs" title="Next in the top 10">
                    <div style={{ display: "grid", gridTemplateColumns: mid ? "1fr 1fr" : "1fr", gap: 10 }}>
                        <Card it={prevIt} href={path + "?id=" + prevIt.id} />
                        <Card it={nextIt} href={path + "?id=" + nextIt.id} />
                    </div>
                </Section>
            </div>
        )
    }

    // Benchmarks: official training sites and Mangystau (not in the top 10)
    return (
        <div ref={ref} style={{ width: "100%", color: C.text, fontFamily: BODY, ...props.style }}>
            <NavRow path={path} listPath={listPath} />
            <div style={{ marginTop: 36 }}>
                <Chip color={m.color}>{"vs " + targetLabel + " · not in the top 10"}</Chip>
                <h1 style={{ fontFamily: HEAD, fontSize: wide ? 52 : mid ? 40 : 32, fontWeight: 700, lineHeight: 1.08, letterSpacing: "-0.02em", margin: "18px 0 0" }}>{it.name}</h1>
                <div style={{ fontSize: 15, color: C.muted, marginTop: 12 }}>{String(it.title).split(":")[0]} · shown with its real rank, for comparison</div>
            </div>
            {it.facts.length ? (
                <Section kicker="Why this place" title="How it matches" mt={44}>
                    {it.facts.map((f: string) => (
                        <p key={f} style={{ fontSize: 15.5, lineHeight: 1.65, color: C.muted, margin: "0 0 10px", maxWidth: 900 }}>{f}</p>
                    ))}
                </Section>
            ) : null}
            {it.sites.length ? (
                <Section kicker="Satellite view" title={it.sites.length > 1 ? "The sites" : "The site"}>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(" + (wide ? Math.min(3, it.sites.length) : mid ? 2 : 1) + ", minmax(0,1fr))", gap: 18 }}>
                        {it.sites.map((s: any) => (
                            <Shot key={s.name} src={s2Url(s.lat, s.lon, 0.25, 640)} alt={"Sentinel-2 view of " + s.name} title={s.name + " · " + fmtLL(s.lat, s.lon)} credit={S2_CREDIT + " · coordinates: " + String(s.coord_source || "").split(":")[0]} />
                        ))}
                    </div>
                </Section>
            ) : null}
            {it.rows.map((r: any) => (
                <div key={r.place} style={{ display: "grid", gridTemplateColumns: wide ? "minmax(0,1.45fr) minmax(0,1fr)" : "1fr", gap: 36, marginTop: 56, alignItems: "start" }}>
                    <Section kicker="7 criteria · NASA / USGS data, 2015–2024" title={r.place} mt={0}>
                        <Criteria r={r} color={m.color} weights={d.weights} wide={mid} />
                        {plain(r) ? (
                            <>
                                <div style={{ fontFamily: MONO, fontSize: 10.5, color: C.subtle, textTransform: "uppercase", letterSpacing: "0.05em", marginTop: 22 }}>{d.aiLabel}</div>
                                <p style={{ fontSize: 14.5, lineHeight: 1.6, color: C.muted, margin: "8px 0 0" }}>{plain(r)}</p>
                            </>
                        ) : null}
                    </Section>
                    <ScoreCard r={r} color={m.color} nCells={d.nCells} />
                </div>
            ))}
            <div style={{ display: "grid", gridTemplateColumns: wide ? "minmax(0,1.45fr) minmax(0,1fr)" : "1fr", gap: 36, marginTop: 56, alignItems: "start" }}>
                {it.notLike.length ? (
                    <Section kicker="Honest limits" title="How it doesn't match" mt={0}>
                        <ul style={{ margin: 0, paddingLeft: 18, color: C.muted, fontSize: 15, lineHeight: 1.7 }}>
                            {it.notLike.map((x: string) => (
                                <li key={x}>{x}</li>
                            ))}
                        </ul>
                    </Section>
                ) : (
                    <div />
                )}
                <Section kicker="Target" title="Compared with" mt={0}>
                    <TargetPanel target={it.target} d={d} />
                </Section>
            </div>
            <Section kicker="Back to the list" title="The top 10">
                <div style={{ display: "grid", gridTemplateColumns: mid ? "1fr 1fr" : "1fr", gap: 10 }}>
                    {d.items.filter((x: any) => x.target === it.target).slice(0, 2).map((x: any) => (
                        <Card key={x.id} it={x} href={path + "?id=" + x.id} />
                    ))}
                </div>
            </Section>
        </div>
    )
}
addPropertyControls(AnalogDetail, {
    previewId: { type: ControlType.String, title: "Preview id", defaultValue: "moon-1" },
    listPath: { type: ControlType.String, title: "List page", defaultValue: "/analogs" },
    detailPath: { type: ControlType.String, title: "Detail page", defaultValue: "/analog" },
})
