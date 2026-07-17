import colorsys
import json
import math
import os
import re
import sys
from urllib.request import Request, urlopen, HTTPError, URLError

from bottle import Bottle, request, response, static_file, template

TLE_STATIC_FILE = os.path.join(os.path.dirname(__file__), 'tle_data.json')
TLE_URL = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle'
TLE_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
R_EARTH = 6371.0
MU = 398600.5

app = Bottle()

_GEO_PREFIXES = [
    'INTELSAT', 'SES ', 'EUTELSAT', 'TELESAT', 'VIASAT',
    'ECHOSTAR', 'HUGHES', 'INMARSAT', 'THURAYA', 'ASIASAT',
    'ARABSAT', 'NILESAT', 'YAMAL', 'EXPRESS-', 'KAZSAT',
    'CHINASAT', 'ZHONGXING', 'GSAT', 'INSAT', 'TELKOM-',
    'PALAPA', 'JCSAT', 'KOREASAT', 'APSTAR',
    'GALAXY ', 'ASTRA ', 'DIRECTV', 'TURKSAT',
    'TELSTAR', 'AMAZONAS', 'OPTUS ', 'NIMIQ ', 'ANIK ',
    'SAUDICOMSAT', 'SAUDISAT', 'THAICOM', 'HISPASAT',
    'HYLAS ', 'HELLAS-SAT', 'THOR ', 'TIANLIAN', 'TIANTONG-',
]

_MAKE_SUB = lambda k, l, m, c, o, z: {'key': k, 'label': l, 'match': m,
    'country': c, 'operator': o, 'name_zh': z}

CATEGORIES = [
    {
        'key': 'communications',
        'label': 'Communications',
        'color': '#4CAF50',
        'subcategories': [
            _MAKE_SUB('starlink', 'Starlink', lambda n: n.startswith('STARLINK'), 'USA', 'SpaceX', '星链'),
            _MAKE_SUB('oneweb', 'OneWeb', lambda n: n.startswith('ONEWEB'), 'UK', 'Eutelsat OneWeb', '一网'),
            _MAKE_SUB('kuiper', 'Kuiper', lambda n: n.startswith('KUIPER'), 'USA', 'Amazon', '柯伊伯'),
            _MAKE_SUB('qianfan', 'Qianfan', lambda n: n.startswith('QIANFAN'), 'China', 'Shanghai Spacecom', '千帆'),
            _MAKE_SUB('hulianwang', 'Hulianwang', lambda n: n.startswith('HULIANWANG'), 'China', 'CNSA', '互联网'),
            _MAKE_SUB('iridium', 'Iridium', lambda n: n.startswith('IRIDIUM') and 'DEB' not in n, 'USA', 'Iridium Communications', '铱星'),
            _MAKE_SUB('globalstar', 'Globalstar', lambda n: n.startswith('GLOBALSTAR'), 'USA', 'Globalstar', '全球星'),
            _MAKE_SUB('orbcomm', 'Orbcomm', lambda n: n.startswith('ORBCOMM'), 'USA', 'Orbcomm', '轨道通信'),
            _MAKE_SUB('gonets', 'Gonets', lambda n: n.startswith('GONETS-M'), 'Russia', 'Gonets Satellite System', '信使'),
            _MAKE_SUB('o3b', 'O3B', lambda n: n.startswith('O3B '), 'Luxembourg', 'SES', 'O3B'),
            _MAKE_SUB('geo_comms', 'GEO Comms', lambda n: any(n.startswith(p) for p in _GEO_PREFIXES), 'Multi', 'Various', '静轨通信'),
            _MAKE_SUB('amateur', 'Amateur Radio', lambda n: any(n.startswith(p) for p in
                ['AO-', 'SO-', 'FO-', 'HO-', 'JO-', 'KO-', 'LO-', 'NO-',
                 'PO-', 'TO-', 'EO-', 'RS-', 'RS ', 'LILACSAT', 'CAS-',
                 'XW-']) or 'OSCAR' in n, 'Multi', 'Amateur', '业余无线电'),
            _MAKE_SUB('other_comms', 'Other Comms', lambda n: any(n.startswith(p) for p in
                ['SWARM ', 'ASTROCAST', 'KEPLER', 'LYNK ', 'MYRIOTA',
                 'HIBER ', 'E-SPACE', 'CONNECTA', 'CENTISPACE']), 'Multi', 'Various', '其他通信'),
        ]
    },
    {
        'key': 'navigation',
        'label': 'Navigation',
        'color': '#2196F3',
        'subcategories': [
            _MAKE_SUB('gps', 'GPS', lambda n: 'NAVSTAR' in n, 'USA', 'US Space Force', 'GPS'),
            _MAKE_SUB('glonass', 'GLONASS', lambda n: 'GLONASS' in n, 'Russia', 'Roscosmos', '格洛纳斯'),
            _MAKE_SUB('galileo', 'Galileo', lambda n: 'GALILEO' in n, 'EU', 'ESA/GSA', '伽利略'),
            _MAKE_SUB('beidou', 'BeiDou', lambda n: n.startswith('BEIDOU'), 'China', 'CNSA', '北斗'),
            _MAKE_SUB('irnss', 'IRNSS', lambda n: n.startswith('IRNSS'), 'India', 'ISRO', '印度导航'),
            _MAKE_SUB('qzss', 'QZSS', lambda n: n.startswith('QZSS'), 'Japan', 'JAXA', '准天顶'),
            _MAKE_SUB('sbas', 'SBAS', lambda n: any(n.startswith(p) for p in
                ['WAAS', 'EGNOS', 'MSAS', 'GAGAN', 'SDCM']), 'Multi', 'Various', '星基增强'),
        ]
    },
    {
        'key': 'earth_obs',
        'label': 'Earth Obs & Weather',
        'color': '#FF9800',
        'subcategories': [
            _MAKE_SUB('planet', 'Planet/Flock', lambda n: any(n.startswith(p) for p in
                ['FLOCK', 'DOVE', 'SKYSAT', 'SUPERDOVE']), 'USA', 'Planet Labs', '行星'),
            _MAKE_SUB('sentinel', 'Sentinel', lambda n: n.startswith('SENTINEL'), 'EU', 'ESA', '哨兵'),
            _MAKE_SUB('landsat', 'Landsat', lambda n: n.startswith('LANDSAT'), 'USA', 'NASA/USGS', '陆地卫星'),
            _MAKE_SUB('noaa_goes', 'NOAA/GOES', lambda n: any(n.startswith(p) for p in
                ['NOAA', 'GOES', 'METOP', 'METEOSAT', 'HIMAWARI',
                 'JPSS', 'ELEKTRO-L', 'METEOR-M']), 'Multi', 'NOAA/EUMETSAT', '气象卫星'),
            _MAKE_SUB('fengyun', 'Fengyun', lambda n: n.startswith('FENGYUN') or n.startswith('FY-'), 'China', 'CMA', '风云'),
            _MAKE_SUB('gaofen', 'Gaofen', lambda n: n.startswith('GAOFEN'), 'China', 'CNSA', '高分'),
            _MAKE_SUB('yaogan', 'Yaogan', lambda n: n.startswith('YAOGAN-'), 'China', 'CNSA', '遥感'),
            _MAKE_SUB('geesat', 'Geespace', lambda n: n.startswith('GEESAT'), 'China', 'Geely', '吉利卫星'),
            _MAKE_SUB('sar', 'SAR', lambda n: any(n.startswith(p) for p in
                ['RADARSAT', 'COSMO-SKYMED', 'TERRASAR', 'TANDEM',
                 'SAOCOM', 'ICEYE-X', 'CAPELLA-', 'UMBRA-', 'RCM-',
                 'SYNCHRONA', 'QPS-SAR', 'SEER-', 'PIESAT']), 'Multi', 'Various', '合成孔径雷达'),
            _MAKE_SUB('other_eo', 'Other EO', lambda n: any(n.startswith(p) for p in
                ['SPOT ', 'PLEIADES', 'KOMPSAT', 'KITSAT', 'IRS ',
                 'CARTOSAT', 'RISAT', 'ALOS', 'CBERS', 'ZIYUAN',
                 'JILIN', 'NUSAT', 'WORLDVIEW', 'GEOEYE', 'QUICKBIRD',
                 'IKONOS', 'AISAT', 'EXACTVIEW', 'VESSELSAT',
                 'TIANHUI', 'YUNHAI-', 'SUPERVIEW', 'ZHUHAI-',
                 'IRIDE', 'KANOPUS-V', 'FORMOSAT', 'NINGXIA-',
                 'CHUANGXIN', 'DONGPO', 'TIANMU-']), 'Multi', 'Various', '其他对地观测'),
        ]
    },
    {
        'key': 'science',
        'label': 'Science & Stations',
        'color': '#9C27B0',
        'subcategories': [
            _MAKE_SUB('iss', 'ISS', lambda n: n.startswith('ISS '), 'Multi', 'International', '国际空间站'),
            _MAKE_SUB('css', 'CSS/Tiangong', lambda n: any(n.startswith(p) for p in
                ['CSS', 'TIANHE', 'WENTIAN', 'MENGTIAN']), 'China', 'CMSA', '中国空间站'),
            _MAKE_SUB('crew_cargo', 'Crew/Cargo', lambda n: any(n.startswith(p) for p in
                ['SOYUZ', 'PROGRESS', 'SHENZHOU', 'TIANZHOU', 'DRAGON',
                 'CYGNUS', 'HTV-']), 'Multi', 'Various', '载人/货运'),
            _MAKE_SUB('observatories', 'Observatories', lambda n: any(n.startswith(p) for p in
                ['HUBBLE', 'CHANDRA', 'XMM', 'Fermi', 'SWIFT', 'NUSTAR',
                 'TESS', 'EUCLID', 'GAIA ', 'SOHO', 'SDO', 'STEREO',
                 'INTEGRAL']), 'Multi', 'NASA/ESA', '天文台'),
            _MAKE_SUB('science_other', 'Other Science', lambda n: any(n.startswith(p) for p in
                ['MMS ', 'THEMIS', 'CLUSTER', 'ACE ', 'WIND ',
                 'RBSP', 'CALIPSO', 'CLOUDSAT', 'SMAP', 'SMOS',
                 'GRACE', 'OCO-', 'GOSAT', 'ICESAT', 'CRYOSAT',
                 'SWOT', 'CYGNSS', 'SENTINEL-5', 'SENTINEL-6',
                 'NICER', 'MAXI', 'LAGEOS', 'LARES', 'STARLETTE',
                 'STELLA', 'SHIJIAN-', 'SWARM B', 'SWARM C',
                 'SWARM A', 'AQUA', 'TERRA', 'AURA']), 'Multi', 'Various', '其他科学'),
        ]
    },
    {
        'key': 'other',
        'label': 'Other',
        'color': '#9E9E9E',
        'subcategories': [
            _MAKE_SUB('tech_demo', 'Tech Demo', lambda n: any(n.startswith(p) for p in
                ['PROBA', 'TECHSAT', 'AEROCUBE', 'PTD', 'LIGHTSAIL',
                 'STPSAT', 'STP-', 'RPP', 'SENSE', 'DARPA', 'SHERPA',
                 'MOMENTUS', 'OTV ', 'X-37', 'SHIYAN', 'ION SCV',
                 'RASSVET-', 'SCS-0', 'APRIZESAT', 'WILDFIRE',
                 'CHECKMATE', 'AERO-CUBE']), 'Multi', 'Various', '技术验证'),
            _MAKE_SUB('military', 'Military/Gov', lambda n: any(n.startswith(p) for p in
                ['USA ', 'NROL', 'SBIRS', 'STSS', 'DSP ', 'AEHF',
                 'MILSTAR', 'MUOS', 'WGS ', 'SKYNET', 'QUASAR',
                 'SDS ', 'DSN ', 'PRAETORIAN', 'SDA_', 'SYRACUSE',
                 'MERIDIAN', 'UFO ', 'SICRAL']), 'Multi', 'Various', '军事/政府'),
            _MAKE_SUB('debris_rb', 'R/B & Debris', lambda n: (n.endswith(' R/B') or n.endswith(' DEB')
                or n.endswith(' AKM') or n.startswith('TRANSPORTER-')
                or n.startswith('BANDWAGON-')
                or bool(re.match(r'^\d{4}-\d{3}[A-Z]+', n))), '-', '-', '碎片/火箭体'),
        ]
    }
]


def _build_flat_patterns():
    flat = []
    for cat in CATEGORIES:
        for sub in cat['subcategories']:
            flat.append({
                'cat_key': cat['key'],
                'cat_label': cat['label'],
                'cat_color': cat['color'],
                'sub_key': sub['key'],
                'sub_label': sub['label'],
                'country': sub.get('country', ''),
                'operator': sub.get('operator', ''),
                'name_zh': sub.get('name_zh', ''),
                'match': sub['match'],
            })
    return flat

FLAT_PATTERNS = _build_flat_patterns()

UNCAT_KEY = 'uncategorized'

# Bright categorical palette (40 colors), all saturated and distinct.
# Sources: D3 schemeSet1, schemeAccent, schemeDark2, Tableau 10.
# Palette interleaving color families so adjacent subs are visually distinct.
_SUB_COLORS = [
    '#1f77b4','#e41a1c','#4daf4a','#ff7f00','#984ea3','#ffff33','#17becf','#e377c2',
    '#386cb0','#d62728','#2ca02c','#f28e2b','#9467bd','#bcbd22','#5254a3','#f781bf',
    '#377eb8','#e15759','#66a61e','#d95f02','#6b6ecf','#edc948','#76b7b2','#e7298a',
    '#4e79a7','#f0027f','#1b9e77','#e6ab02','#7570b3','#fdc086','#7fc97f','#98df8a',
    '#beaed4','#c5b0d5','#59a14f','#a65628','#8c564b','#9c755f','#bf5b17','#a6761d',
]

def _assign_sub_colors():
    all_subs = []
    for cat in CATEGORIES:
        for sub in cat['subcategories']:
            all_subs.append(sub)
    for i, sub in enumerate(all_subs):
        sub['color'] = _SUB_COLORS[i % 40]

_assign_sub_colors()

_assign_sub_colors()


_SUB_RANGES = {}

def _compute_ranges():
    cached = load_cache()
    if not cached:
        return
    ranges = {}
    for raw in cached:
        sat = enrich(dict(raw))
        sk = sat['sub_key']
        h = sat['h_mean']
        if h is None:
            continue
        if sk not in ranges:
            ranges[sk] = [h, h]
        else:
            if h < ranges[sk][0]:
                ranges[sk][0] = h
            if h > ranges[sk][1]:
                ranges[sk][1] = h
    global _SUB_RANGES
    _SUB_RANGES = ranges

def classify(name):
    for p in FLAT_PATTERNS:
        if p['match'](name):
            return {
                'cat_key': p['cat_key'],
                'cat_label': p['cat_label'],
                'cat_color': p['cat_color'],
                'sub_key': p['sub_key'],
                'sub_label': p['sub_label'],
                'country': p['country'],
                'operator': p['operator'],
                'name_zh': p['name_zh'],
            }
    return {
        'cat_key': UNCAT_KEY,
        'cat_label': 'Uncategorized',
        'cat_color': '#E0E0E0',
        'sub_key': UNCAT_KEY,
        'sub_label': 'Uncategorized',
        'country': '',
        'operator': '',
        'name_zh': '',
    }


def compute_altitude(line1, line2):
    try:
        n = float(line2[52:63].strip())
        e_str = '0.' + line2[26:33].strip()
        e = float(e_str)
        n_rad = n * 2 * math.pi / 86400.0
        a = (MU / (n_rad ** 2)) ** (1.0 / 3.0)
        h_mean = a - R_EARTH
        h_perigee = a * (1 - e) - R_EARTH
        h_apogee = a * (1 + e) - R_EARTH
        return round(h_mean, 2), round(h_perigee, 2), round(h_apogee, 2)
    except (ValueError, IndexError):
        return None, None, None


def _tle_fetch(url):
    req = Request(url, headers={'User-Agent': TLE_UA, 'Accept': 'text/plain,*/*'})
    try:
        with urlopen(req, timeout=30) as r:
            return r.read().decode('utf-8')
    except HTTPError as e:
        return e.read().decode('utf-8')
    except URLError:
        return ''


def _parse_tle(text):
    lines = text.strip().split('\n')
    out = []
    i = 0
    while i + 2 < len(lines):
        name = lines[i].strip()
        l1 = lines[i + 1].strip()
        l2 = lines[i + 2].strip()
        if l1.startswith('1 ') and l2.startswith('2 '):
            out.append({'name': name, 'line1': l1, 'line2': l2})
            i += 3
        else:
            i += 1
    return out


def load_cache():
    if os.path.exists(TLE_STATIC_FILE):
        with open(TLE_STATIC_FILE, 'r') as f:
            return json.load(f)
    return None


def save_cache(data):
    with open(TLE_STATIC_FILE, 'w') as f:
        json.dump(data, f)


def enrich(sat):
    cls = classify(sat['name'])
    h_mean, h_perigee, h_apogee = compute_altitude(sat['line1'], sat['line2'])
    sat['cat_key'] = cls['cat_key']
    sat['cat_label'] = cls['cat_label']
    sat['cat_color'] = cls['cat_color']
    sat['sub_key'] = cls['sub_key']
    sat['sub_label'] = cls['sub_label']
    sat['country'] = cls['country']
    sat['operator'] = cls['operator']
    sat['name_zh'] = cls['name_zh']
    sat['h_mean'] = h_mean
    sat['h_perigee'] = h_perigee
    sat['h_apogee'] = h_apogee
    try:
        norad = sat['line1'][2:7].strip()
        sat['norad'] = int(norad) if norad else None
    except (ValueError, IndexError):
        sat['norad'] = None
    return sat


_compute_ranges()


# bottle has no enable_cors decorator built-in
@app.hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'


@app.route('/')
def index():
    return static_file('index.html', root=os.path.join(os.path.dirname(__file__), 'templates'))


@app.route('/update', method=['POST', 'OPTIONS'])
def do_update():
    text = _tle_fetch(TLE_URL)
    parsed = _parse_tle(text)
    if parsed:
        save_cache(parsed)
        return json.dumps({'status': 'ok', 'count': len(parsed)})
    return json.dumps({'status': 'error', 'message': 'Failed to parse TLE data'})


@app.route('/api/data')
def api_data():
    cached = load_cache()
    if cached is None:
        return json.dumps({'status': 'error', 'message': 'No TLE data. POST /update first.'})
    result = [enrich(dict(s)) for s in cached]
    return json.dumps({'status': 'ok', 'count': len(result), 'satellites': result})


@app.route('/api/categories')
def api_categories():
    clean = []
    for cat in CATEGORIES:
        subs = [{'key': s['key'], 'label': s['label'],
                 'country': s.get('country', ''), 'operator': s.get('operator', ''),
                 'name_zh': s.get('name_zh', ''),
                 'color': s['color'],
                 'range_min': round(_SUB_RANGES.get(s['key'], [0,0])[0]),
                 'range_max': round(_SUB_RANGES.get(s['key'], [0,0])[1])}
                for s in cat['subcategories']]
        clean.append({
            'key': cat['key'],
            'label': cat['label'],
            'color': cat['color'],
            'subcategories': subs,
        })
    return json.dumps({'status': 'ok', 'categories': clean})


@app.route('/api/analyze', method=['POST', 'OPTIONS'])
def api_analyze():
    cached = load_cache()
    if cached is None:
        return json.dumps({'status': 'error', 'message': 'No TLE data.'})
    body = request.json or {}
    selected_subs = set(body.get('selected_subcategories', []))

    enriched = [enrich(dict(s)) for s in cached]

    filtered = [s for s in enriched if s['sub_key'] in selected_subs and s['h_mean'] is not None]

    if not filtered:
        return json.dumps({'status': 'ok', 'bins': [], 'count': 0})

    bin_width = float(body.get('bin_width', 10))

    min_h = min(s['h_mean'] for s in filtered)
    max_h = max(s['h_mean'] for s in filtered)

    bin_start = math.floor(min_h / bin_width) * bin_width
    bin_end = math.ceil(max_h / bin_width) * bin_width

    num_bins = max(1, int((bin_end - bin_start) / bin_width))

    bins = []
    for i in range(num_bins):
        lo = bin_start + i * bin_width
        hi = lo + bin_width
        bins.append({
            'min': lo,
            'max': hi,
            'count': 0,
            'categories': {},
            'subcategories': {},
        })

    for sat in filtered:
        idx = int((sat['h_mean'] - bin_start) / bin_width)
        if 0 <= idx < num_bins:
            bins[idx]['count'] += 1
            ck = sat['cat_key']
            bins[idx]['categories'][ck] = bins[idx]['categories'].get(ck, 0) + 1
            sk = sat['sub_key']
            bins[idx]['subcategories'][sk] = bins[idx]['subcategories'].get(sk, 0) + 1

    collapsed_bins = []
    empty_run = []
    for b in bins:
        if b['count'] == 0 and not b['subcategories']:
            empty_run.append(b)
        else:
            if empty_run:
                if len(empty_run) <= 3:
                    collapsed_bins.extend(empty_run)
                else:
                    mid = len(empty_run) // 2
                    for idx in [0, mid, -1]:
                        eb = dict(empty_run[idx])
                        eb['collapsed'] = True
                        collapsed_bins.append(eb)
                empty_run = []
            collapsed_bins.append(b)
    if empty_run:
        if len(empty_run) <= 3:
            collapsed_bins.extend(empty_run)
        else:
            mid = len(empty_run) // 2
            for idx in [0, mid, -1]:
                eb = dict(empty_run[idx])
                eb['collapsed'] = True
                collapsed_bins.append(eb)

    return json.dumps({
        'status': 'ok',
        'bins': collapsed_bins,
        'count': len(filtered),
        'total': len(enriched),
        'bin_width': bin_width,
        'range_min': bin_start,
        'range_min_original': round(min_h),
        'range_max_original': round(max_h),
    })


def _tle_epoch(line1):
    try:
        epoch_str = line1[17:32].strip()
        y = int(epoch_str[:2])
        doy = float(epoch_str[2:])
        year = 2000 + y if y < 57 else 1900 + y
        from datetime import datetime, timedelta
        dt = datetime(year, 1, 1) + timedelta(days=doy - 1)
        return dt.isoformat()[:19]
    except:
        return ''


@app.route('/api/tle_info')
def api_tle_info():
    cached = load_cache()
    if not cached:
        return json.dumps({'status': 'ok', 'epoch': '', 'count': 0})
    latest = ''
    for s in cached:
        e = _tle_epoch(s['line1'])
        if e > latest:
            latest = e
    return json.dumps({'status': 'ok', 'epoch': latest, 'count': len(cached)})


@app.route('/api/update_status')
def api_update_status():
    cached = load_cache()
    if cached:
        latest = ''
        for s in cached:
            e = _tle_epoch(s['line1'])
            if e > latest:
                latest = e
        return json.dumps({'status': 'ok', 'cached': True, 'count': len(cached), 'epoch': latest})
    return json.dumps({'status': 'ok', 'cached': False, 'count': 0})


if __name__ == '__main__':
    try:
        from cheroot.wsgi import Server as CherootServer
        server = CherootServer(('0.0.0.0', int(os.environ.get('PORT', '15001'))), app, numthreads=10)
        print(f'Listening on http://0.0.0.0:{os.environ.get("PORT", "15001")} (cheroot, 10 threads)')
        server.start()
    except ImportError:
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '15001')), debug=True)
