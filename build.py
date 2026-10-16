#!/usr/bin/env python3
"""Generate the static pages of Beautiful Danish Data from data/*.json.

Run `python3 build.py` after editing data/papers.json or data/variables.json.
"""
import html
import re
import json
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAPERS = json.loads((ROOT / "data" / "papers.json").read_text())
VARS = json.loads((ROOT / "data" / "variables.json").read_text())

SITE = "https://zhurt0.github.io/beautiful-danish-data/"
HOME = "https://zhurt0.github.io/rentianzhu/"

GROUPS = [
    ("top5", "Top 5", "American Economic Review, Quarterly Journal of Economics, Journal of Political Economy, Econometrica and Review of Economic Studies."),
    ("aeri", "AER: Insights", "American Economic Review: Insights, the AER's short-paper journal."),
    ("aej", "American Economic Journals", "American Economic Journal: Applied Economics, Economic Policy and Macroeconomics."),
    ("restat", "Review of Economics and Statistics", ""),
    ("ej", "Economic Journal", ""),
    ("jole", "Journal of Labor Economics", "The leading field journal in labour economics."),
    ("jpube", "Journal of Public Economics", "The leading field journal in public economics."),
]

THEMES = [
    ("taxation", "Taxation and public finance", "Behavioural responses to income, wealth and audit policy, identified from reforms and experiments on full-population tax records."),
    ("household-finance", "Household finance, saving and consumption", "Saving, borrowing, consumption responses and wealth dynamics, built on third-party reported assets, debt and imputed consumption."),
    ("labor", "Labour markets, wages and sorting", "Search and matching, wage dynamics and who works with whom, using matched employer-employee data."),
    ("trade", "Trade and offshoring", "Firm-level imports and exports by product linked to the wages of the workers inside those firms."),
    ("firms", "Firms, ownership and innovation", "Firm accounts, management and family ownership, and product innovation."),
    ("gender", "Gender and the family", "Child penalties and the family as the unit of labour supply, health behaviour and insurance."),
    ("family", "Family responses and insurance", "How spouses and children respond to shocks hitting another family member."),
    ("health", "Health", "Hospital diagnoses, prescriptions and births as shocks and as outcomes."),
    ("migration", "Migration, neighbourhoods and refugees", "Refugee dispersal as quasi-random assignment, immigration effects on natives, and benefit cuts."),
    ("crime", "Crime", "Charges and convictions as outcomes of neighbourhoods, school timing and welfare policy."),
    ("children", "Children, intergenerational mobility and skills", "What is transmitted across generations: wealth, earnings, financial trouble, health and skills."),
    ("education", "Education", "Student aid, school starting age and schooling outcomes."),
    ("inequality", "Inequality and fairness", "Top wealth, tax evasion, sibling correlations and what people believe about their own position."),
    ("politics", "Political economy", "Electoral responses to immigration."),
    ("macro", "Macroeconomics and expectations", "Disaggregated accounts, expectations and firm pricing built from Danish micro data."),
    ("housing", "Housing", "Home ownership and labour market behaviour."),
    ("methods", "Measurement and methods", "How to build variables, such as consumption, from register data."),
    ("innovation", "Innovation", "Product innovation and growth at the firm level."),
]
THEME_NAME = {k: n for k, n, _ in THEMES}
PAPER_BY_ID = {p["id"]: p for p in PAPERS}
LEVEL_LABEL = {"individual": "Individual", "firm": "Firm", "both": "Individual + firm"}


def e(s):
    return html.escape(s, quote=True)


def scholar(title):
    return "https://scholar.google.com/scholar?q=" + urllib.parse.quote_plus(title)


def head(title, description, canonical):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{e(title)}</title>
    <meta name="description" content="{e(description)}">
    <meta name="author" content="Rentian Zhu">
    <link rel="canonical" href="{SITE}{canonical}">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Beautiful Danish Data">
    <meta property="og:title" content="{e(title)}">
    <meta property="og:description" content="{e(description)}">
    <meta property="og:url" content="{SITE}{canonical}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="css/styles.css">
    <link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
</head>
<body>
"""


def nav(active):
    items = [("index.html", "Summary"), ("themes.html", "Themes"), ("samples.html", "Data & samples"), ("landscape.html", "3D data landscape"), ("variables.html", "Variable map")]
    lis = ""
    for href, label in items:
        cls = ' class="active"' if href == active else ""
        lis += f'<li><a href="{href}"{cls}>{label}</a></li>'
    return f"""    <header>
        <div class="container">
            <p class="eyebrow"><a href="{HOME}">Rentian Zhu</a> &rsaquo; Useful links</p>
            <h1><a href="index.html">Beautiful Danish Data</a></h1>
            <p class="tagline">A field guide to economics published with Danish administrative data</p>
        </div>
    </header>
    <nav>
        <div class="container">
            <ul>{lis}<li><a href="https://github.com/Zhurt0/beautiful-danish-data" target="_blank" rel="noopener">GitHub</a></li></ul>
        </div>
    </nav>
"""


FOOTER = f"""    <footer>
        <div class="container">
            <p>Maintained by <a href="{HOME}">Rentian Zhu</a>, Copenhagen Business School. Summaries are my own reading of each paper. Corrections and additions are welcome as pull requests on <a href="https://github.com/Zhurt0/beautiful-danish-data" target="_blank" rel="noopener">GitHub</a>.</p>
        </div>
    </footer>
</body>
</html>
"""


NOT_FOUND = "Not stated in the sources checked"


def short_cite(p):
    first = p["authors"].split(",")[0].split(" and ")[0].split()[-1]
    n = len([a for a in re.split(r",| and ", p["authors"]) if a.strip()])
    return f"{first}{' et al.' if n > 2 else (' and ' + p['authors'].split(' and ')[-1].split()[-1] if n == 2 else '')} ({p['year']})"


def facts(p):
    rows = []
    rows.append(("Data", ", ".join(e(d) for d in p["data"])))
    if p.get("variables"):
        rows.append(("Key variables", "<ul>" + "".join(f"<li>{e(v)}</li>" for v in p["variables"]) + "</ul>"))
    rows.append(("Period", e(p["period"]) if p.get("period") else f'<span class="na">{NOT_FOUND}</span>'))
    if p.get("sample_size"):
        size = f'<strong>{e(p["sample_size"])}</strong>'
    else:
        size = f'<span class="na">{NOT_FOUND}</span>'
    desc = f' <span class="desc">{e(p["sample"])}</span>' if p.get("sample") else ""
    src = ""
    if p.get("sample_source"):
        tag = " (abstract)" if p.get("sample_confidence") == "abstract" else ""
        src = f' <a class="src" href="{e(p["sample_source"])}" target="_blank" rel="noopener">source{tag}</a>'
    rows.append(("Sample", size + desc + src))
    return '                    <dl class="facts">\n' + "".join(
        f'                        <div><dt>{k}</dt><dd>{v}</dd></div>\n' for k, v in rows
    ) + "                    </dl>\n"


def paper_card(p, show_themes=True):
    themes = ""
    if show_themes:
        themes = '<p class="tags">' + " ".join(
            f'<a class="tag" href="themes.html#{t}">{e(THEME_NAME[t])}</a>' for t in p["themes"]
        ) + "</p>"
    return f"""                <article class="paper" id="{p['id']}">
                    <h4><a href="{scholar(p['title'])}" target="_blank" rel="noopener">{e(p['title'])}</a></h4>
                    <p class="meta">{e(p['authors'])} &middot; <em>{e(p['journal'])}</em>, {p['year']} &middot; <span class="level">{LEVEL_LABEL[p['level']]}</span></p>
                    <p class="summary">{e(p['summary'])}</p>
{facts(p)}{themes}
                </article>
"""


def build_index():
    counts = {g: sum(1 for p in PAPERS if p["group"] == g) for g, _, _ in GROUPS}
    out = head(
        "Beautiful Danish Data | Papers using Danish administrative data",
        "Summaries of Top 5, AEJ, Review of Economics and Statistics and Economic Journal papers that use Danish administrative register data, organised by journal, by theme and by variable.",
        "",
    )
    out += nav("index.html")
    out += f"""    <section class="section intro">
        <div class="container">
            <h2 class="section-title">Why this page</h2>
            <p>Denmark links every resident, firm, hospital visit, tax return and job to a single identifier, and lets researchers work with the whole population from the 1980s onwards. This page is a reading list of the economics that has come out of that infrastructure in the top general-interest journals and in the two leading field journals for labour and public economics: what question each paper asks, what it finds, and which registers it is built from.</p>
            <p>The list covers {len(PAPERS)} papers. It was assembled by searching Crossref for every article in these journals whose title or abstract mentions Denmark or Danish data, and by going through the publication lists of the main Danish research groups and authors, then checking each paper. It excludes <em>AEA Papers and Proceedings</em>, finance journals and papers that only use Danish data as one country among many. It will still miss papers whose abstracts do not name the country, so additions are welcome. Each paper lists its datasets, key variables, data period and sample size, and the <a href="samples.html">Data &amp; samples</a> page puts these in one sortable table. The <a href="themes.html">Themes</a> page regroups the same papers by topic, and the <a href="variables.html">Variable map</a> lists the registers and variables they rely on, at the individual and the firm level. If a paper is missing or a summary is wrong, open an issue or a pull request on GitHub.</p>
            <ul class="counts">
{"".join(f'                <li><a href="#{g}">{e(n)}</a><span>{counts[g]}</span></li>' + chr(10) for g, n, _ in GROUPS)}            </ul>
        </div>
    </section>
"""
    for g, name, blurb in GROUPS:
        papers = sorted((p for p in PAPERS if p["group"] == g), key=lambda p: (-p["year"], p["authors"]))
        out += f"""    <section class="section" id="{g}">
        <div class="container">
            <h2 class="section-title">{e(name)}</h2>
            {"<p class='blurb'>" + e(blurb) + "</p>" if blurb else ""}
            <div class="papers">
"""
        out += "".join(paper_card(p) for p in papers)
        out += """            </div>
        </div>
    </section>
"""
    out += FOOTER
    return out


def build_themes():
    out = head(
        "Themes | Beautiful Danish Data",
        "The same Danish-register papers grouped by theme: taxation, household finance, labour markets, trade, family, health, migration, crime, children and inequality.",
        "themes.html",
    )
    out += nav("themes.html")
    used = [(k, n, b) for k, n, b in THEMES if any(k in p["themes"] for p in PAPERS)]
    out += """    <section class="section intro">
        <div class="container">
            <h2 class="section-title">By theme</h2>
            <p>A paper can appear under more than one theme. Within each theme, papers are listed from newest to oldest.</p>
            <ul class="toc">
"""
    for k, n, _ in used:
        c = sum(1 for p in PAPERS if k in p["themes"])
        out += f'                <li><a href="#{k}">{e(n)}</a><span>{c}</span></li>\n'
    out += """            </ul>
        </div>
    </section>
"""
    for k, n, b in used:
        papers = sorted((p for p in PAPERS if k in p["themes"]), key=lambda p: (-p["year"], p["authors"]))
        out += f"""    <section class="section" id="{k}">
        <div class="container">
            <h2 class="section-title">{e(n)}</h2>
            <p class="blurb">{e(b)}</p>
            <div class="papers">
"""
        out += "".join(paper_card(p, show_themes=False) for p in papers)
        out += """            </div>
        </div>
    </section>
"""
    out += FOOTER
    return out


def register_block(r):
    rows = "".join(
        f"                    <tr><td><code>{e(v)}</code></td><td>{e(d)}</td></tr>\n" for v, d in r["variables"]
    )
    used = ""
    if r["used_by"]:
        links = ", ".join(
            f'<a href="index.html#{pid}">{e(PAPER_BY_ID[pid]["authors"].split(",")[0].split(" and ")[0].split()[-1])} ({PAPER_BY_ID[pid]["year"]})</a>'
            for pid in r["used_by"] if pid in PAPER_BY_ID
        )
        used = f'                <p class="used-by"><strong>Used by:</strong> {links}</p>\n'
    return f"""            <div class="register">
                <h3>{e(r['register'])}</h3>
                <p class="what">{e(r['what'])}</p>
                <table>
                    <thead><tr><th>Variable</th><th>Meaning</th></tr></thead>
                    <tbody>
{rows}                    </tbody>
                </table>
{used}            </div>
"""


def build_variables():
    out = head(
        "Variable map | Beautiful Danish Data",
        "A map of Statistics Denmark registers and variables used in the papers, at the individual level (BEF, IND, FORM, IDA, BFL, DREAM, UDDA, LPR, LMDB, MFR, DOD, crime) and the firm level (FIRM, FIRE, FIDA, UHDI, VAT, CVR, patents).",
        "variables.html",
    )
    out += nav("variables.html")
    out += """    <section class="section intro">
        <div class="container">
            <h2 class="section-title">Variable map</h2>
            <p>Statistics Denmark delivers data as registers, one per topic, that all share the personal identifier (<code>PNR</code>) on the individual side and the firm identifier (<code>CVRNR</code>) on the firm side. The two sides are joined through the employer link in IDA, FIDA or the monthly payroll data. The map below lists the registers behind the papers on this site, the variables that matter most, and which papers use each register.</p>
            <p class="note">Variable names follow Statistics Denmark's documentation of high-quality variables, but names and version suffixes (such as <code>_13</code>) change between years and projects. Treat the codes as pointers and check the current documentation at <a href="https://www.dst.dk/da/TilSalg/Forskningsservice/Dokumentation/hoejkvalitetsvariable" target="_blank" rel="noopener">dst.dk</a> before writing code.</p>
            <ul class="toc">
                <li><a href="#individual">Individual level</a><span>""" + str(len(VARS["individual"])) + """ registers</span></li>
                <li><a href="#firm">Firm level</a><span>""" + str(len(VARS["firm"])) + """ registers</span></li>
                <li><a href="#bridge">Linking the two</a></li>
            </ul>
        </div>
    </section>
    <section class="section" id="individual">
        <div class="container">
            <h2 class="section-title">Individual level</h2>
            <p class="blurb">Keyed on <code>PNR</code>. One row per person per year unless noted.</p>
"""
    out += "".join(register_block(r) for r in VARS["individual"])
    out += """        </div>
    </section>
    <section class="section" id="firm">
        <div class="container">
            <h2 class="section-title">Firm level</h2>
            <p class="blurb">Keyed on <code>CVRNR</code> (legal unit) and <code>ARBNR</code> (workplace). One row per firm per year unless noted.</p>
"""
    out += "".join(register_block(r) for r in VARS["firm"])
    out += """        </div>
    </section>
    <section class="section" id="bridge">
        <div class="container">
            <h2 class="section-title">Linking the two</h2>
            <div class="register">
                <table>
                    <thead><tr><th>You have</th><th>You want</th><th>Go through</th></tr></thead>
                    <tbody>
                        <tr><td>A worker (<code>PNR</code>)</td><td>Their employer's accounts</td><td>IDAN or FIDA gives <code>CVRNR</code> for the November job; BFL gives it monthly. Then join FIRM/FIRE on <code>CVRNR</code> and year.</td></tr>
                        <tr><td>A firm (<code>CVRNR</code>)</td><td>All its workers and their wages</td><td>FIDA or IDAN filtered on <code>CVRNR</code> gives the <code>PNR</code> set. Join IND for annual earnings or BFL for monthly wages and hours.</td></tr>
                        <tr><td>A firm</td><td>Its CEO's or owner's family</td><td>Company registers give the CEO's <code>PNR</code>; BEF gives parents, spouse and children.</td></tr>
                        <tr><td>A worker</td><td>Co-workers at the same establishment</td><td>IDAN on <code>ARBNR</code> and year, not <code>CVRNR</code>, since a firm can have many workplaces.</td></tr>
                        <tr><td>A worker's job history</td><td>Firm-level trade exposure</td><td>Job spells from IDAN/BFL joined to UHDI on <code>CVRNR</code> and year, as in Hummels et al. (2014).</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </section>
"""
    out += FOOTER
    return out


def build_samples():
    out = head(
        "Data & samples | Beautiful Danish Data",
        "Sample periods, sample sizes and datasets of every paper in Beautiful Danish Data, in one sortable table.",
        "samples.html",
    )
    out += nav("samples.html")
    known = sum(1 for p in PAPERS if p.get("sample_size"))
    out += f"""    <section class="section intro">
        <div class="container">
            <h2 class="section-title">Data &amp; samples</h2>
            <p>Every paper in one table: the years its data cover, the size of its main estimation sample and the registers it draws on. Click a column header to sort, or type to filter. Sample sizes are copied from each paper or its working-paper version; the source link on the paper's card says where. Where neither the paper nor its abstract states a figure, the cell is left blank rather than estimated.</p>
            <p class="note">{known} of {len(PAPERS)} papers have a stated sample size. Sample sizes are not comparable across papers: some count people, others person-years, firms or jobs.</p>
        </div>
    </section>
    <section class="section">
        <div class="container">
            <input id="filter" class="filter" type="search" placeholder="Filter by author, title, register or journal" aria-label="Filter table">
            <div class="table-wrap">
            <table id="samples" class="sortable">
                <thead><tr><th data-k="cite">Paper</th><th data-k="journal">Journal</th><th data-k="period">Period</th><th data-k="size">Sample size</th><th data-k="level">Level</th><th data-k="data">Data</th></tr></thead>
                <tbody>
"""
    for p in sorted(PAPERS, key=lambda p: (-p["year"], p["authors"])):
        size = e(p["sample_size"]) if p.get("sample_size") else '<span class="na">&ndash;</span>'
        period = e(p["period"]) if p.get("period") else '<span class="na">&ndash;</span>'
        dl = "<ul>" + "".join(f"<li>{e(d)}</li>" for d in p["data"]) + "</ul>"
        out += (f'                    <tr><td data-label="Paper"><a href="index.html#{p["id"]}">{e(short_cite(p))}</a><br><span class="t">{e(p["title"])}</span></td>'
                f'<td data-label="Journal">{e(p["journal"])}</td><td data-label="Period">{period}</td><td data-label="Sample size">{size}</td><td data-label="Level">{LEVEL_LABEL[p["level"]]}</td>'
                f'<td class="d" data-label="Data">{dl}</td></tr>\n')
    out += """                </tbody>
            </table>
            </div>
        </div>
    </section>
    <script>
    (function () {
        var table = document.getElementById('samples');
        var body = table.tBodies[0];
        var rows = Array.prototype.slice.call(body.rows);
        var dir = {};
        function key(row, i) {
            var t = row.cells[i].innerText.trim();
            if (i === 2) { var m = t.match(/\\d{4}/); return m ? +m[0] : 9999; }
            if (i === 3) {
                var x = t.replace(/,/g, '').match(/([\\d.]+)\\s*(million|billion)?/i);
                if (!x) return -1;
                var v = parseFloat(x[1]);
                if (x[2]) v *= /billion/i.test(x[2]) ? 1e9 : 1e6;
                return v;
            }
            return t.toLowerCase();
        }
        Array.prototype.forEach.call(table.tHead.rows[0].cells, function (th, i) {
            th.addEventListener('click', function () {
                dir[i] = !dir[i];
                rows.sort(function (a, b) {
                    var ka = key(a, i), kb = key(b, i);
                    if (ka < kb) return dir[i] ? -1 : 1;
                    if (ka > kb) return dir[i] ? 1 : -1;
                    return 0;
                });
                rows.forEach(function (r) { body.appendChild(r); });
            });
        });
        document.getElementById('filter').addEventListener('input', function () {
            var q = this.value.toLowerCase();
            rows.forEach(function (r) { r.style.display = r.innerText.toLowerCase().indexOf(q) === -1 ? 'none' : ''; });
        });
    })();
    </script>
"""
    out += FOOTER
    return out


REG_SHORT = {
    "BEF — Population register": "Population (BEF)",
    "IND — Income register": "Income (IND)",
    "FORM — Wealth register": "Wealth (FORM)",
    "IDA / IDAN / IDAP — Integrated labour market database": "Labour market (IDA)",
    "AKM — Labour market classification": "Labour status (AKM/RAS)",
    "BFL / eIndkomst — Monthly payroll": "Monthly payroll (BFL)",
    "DREAM — Public transfers (weekly)": "Transfers (DREAM)",
    "UDDA — Education register": "Education (UDDA)",
    "LPR — National Patient Register": "Hospital (LPR)",
    "LMDB — Prescription register": "Prescriptions (LMDB)",
    "MFR — Medical Birth Register": "Births (MFR)",
    "DOD — Death register": "Deaths (DOD)",
    "KRAF / KRSI — Crime registers": "Crime (KRAF/KRSI)",
    "VNDS / Residence histories": "Migration and addresses",
    "FIRM / FIRE — Firm statistics and Accounts Statistics": "Firm accounts (FIRM/FIRE)",
    "FIDA — Firm–employee link": "Firm–worker link (FIDA)",
    "UHDI / UHDM — Foreign trade by firm": "Foreign trade (UHDI)",
    "VNDS / Moms — VAT-based turnover": "VAT turnover",
    "Company registers (CVR, ownership, management)": "Company registers (CVR)",
    "Patents and R&D (external, linked by firm)": "Patents and R&D",
}
TIERS = [("Top 5 and AER: Insights", {"top5", "aeri"}),
         ("AEJ, ReStat and Economic Journal", {"aej", "restat", "ej"}),
         ("JOLE and JPubE", {"jole", "jpube"})]


def landscape_data():
    regs = [REG_SHORT.get(r["register"], r["register"]) for r in VARS["individual"] + VARS["firm"]] + ["Other data only"]
    uses = {}
    for r in VARS["individual"] + VARS["firm"]:
        for pid in r["used_by"]:
            uses.setdefault(pid, []).append(REG_SHORT.get(r["register"], r["register"]))
    rows, skipped = [], []
    for p in PAPERS:
        yrs = [int(y) for y in re.findall(r"(?<!\d)(19[0-9]{2}|20[0-2][0-9])(?!\d)", p.get("period") or "")]
        yrs = [y for y in yrs if 1900 <= y <= 2026]
        if not yrs:
            skipped.append(p["id"]); continue
        tier = next(i for i, (_, g) in enumerate(TIERS) if p["group"] in g)
        rows.append(dict(id=p["id"], cite=short_cite(p), title=p["title"], journal=p["journal"],
                         period=p["period"], size=p.get("sample_size") or "not stated",
                         a=min(yrs), b=max(yrs), regs=uses.get(p["id"]) or ["Other data only"], tier=tier))
    rows.sort(key=lambda r: (r["a"], r["b"], r["cite"]))
    for i, r in enumerate(rows):
        r["z"] = i + 1
    return regs, rows, skipped


def build_landscape():
    regs, rows, skipped = landscape_data()
    out = head(
        "3D data landscape | Beautiful Danish Data",
        "A 3D view of which Danish registers each paper uses and which years its data cover, with papers stacked above a year-by-register base.",
        "landscape.html",
    )
    out += nav("landscape.html")
    payload = json.dumps(dict(regs=regs, rows=rows, tiers=[t for t, _ in TIERS]), ensure_ascii=False)
    out += f"""    <section class="section intro">
        <div class="container">
            <h2 class="section-title">3D data landscape</h2>
            <p>The floor of the chart is a grid of years by registers, shaded by how many papers use each register in each year. Every paper floats above it as a layer: one line per register it uses, running from the first to the last year of its data. Papers are stacked by the year their data start, so the oldest data sit at the bottom.</p>
            <p class="note">Drag to rotate, scroll to zoom, hover a line for the paper, click it to open the paper's entry. Click a legend item to hide a journal tier. {len(rows)} of {len(PAPERS)} papers are shown; {len(skipped)} are left out because their data period is not stated. The <a href="samples.html">Data &amp; samples</a> table lists the same information as text.</p>
        </div>
    </section>
    <section class="section viz-section">
        <div class="container">
            <div id="landscape" class="viz" role="img" aria-label="3D chart of papers by data period and register"></div>
        </div>
    </section>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.35.3/plotly.min.js"></script>
    <script>
    (function () {{
        var D = {payload};
        var SERIES = ['#2a78d6', '#eb6834', '#1baf7a'];
        var RAMP = [[0, '#f4f8fd'], [0.15, '#cde2fb'], [0.35, '#86b6ef'], [0.6, '#3987e5'], [0.8, '#1c5cab'], [1, '#0d366b']];
        var regIndex = {{}};
        D.regs.forEach(function (r, i) {{ regIndex[r] = i; }});

        var traces = D.tiers.map(function (name, t) {{
            return {{ type: 'scatter3d', mode: 'lines', name: name, x: [], y: [], z: [], text: [], customdata: [],
                     line: {{ color: SERIES[t], width: 5 }}, hovertemplate: '%{{text}}<extra></extra>' }};
        }});
        D.rows.forEach(function (r) {{
            var tr = traces[r.tier];
            var label = '<b>' + r.cite + '</b><br>' + r.title + '<br>' + r.journal +
                        '<br>Period: ' + r.period + '<br>Sample: ' + r.size;
            r.regs.forEach(function (reg) {{
                var y = regIndex[reg];
                for (var yr = r.a; yr <= r.b; yr++) {{
                    tr.x.push(yr); tr.y.push(y); tr.z.push(r.z);
                    tr.text.push(label + '<br>Register: ' + reg); tr.customdata.push(r.id);
                }}
                tr.x.push(null); tr.y.push(null); tr.z.push(null); tr.text.push(null); tr.customdata.push(null);
            }});
        }});

        var y0 = 9999, y1 = 0;
        D.rows.forEach(function (r) {{ y0 = Math.min(y0, r.a); y1 = Math.max(y1, r.b); }});
        var years = []; for (var y = y0; y <= y1; y++) years.push(y);
        var counts = D.regs.map(function () {{ return years.map(function () {{ return 0; }}); }});
        D.rows.forEach(function (r) {{
            r.regs.forEach(function (reg) {{
                for (var yr = r.a; yr <= r.b; yr++) counts[regIndex[reg]][yr - y0] += 1;
            }});
        }});
        var base = {{
            type: 'surface', name: 'Papers per year and register', showlegend: false,
            x: years, y: D.regs.map(function (_, i) {{ return i; }}),
            z: D.regs.map(function () {{ return years.map(function () {{ return 0; }}); }}),
            surfacecolor: counts, colorscale: RAMP, cmin: 0,
            colorbar: {{ title: {{ text: 'Papers using<br>register that year', font: {{ size: 12 }} }}, thickness: 12, len: 0.55, x: 1.0, tickfont: {{ size: 11 }} }},
            customdata: counts.map(function (row, i) {{ return row.map(function () {{ return D.regs[i]; }}); }}),
            hovertemplate: '%{{customdata}}<br>%{{x}}: %{{surfacecolor}} papers<extra></extra>',
            contours: {{ x: {{ show: false }}, y: {{ show: false }}, z: {{ show: false }} }}
        }};

        var axis = {{ gridcolor: '#e1e0d9', zerolinecolor: '#c3c2b7', linecolor: '#c3c2b7', tickfont: {{ color: '#52514e', size: 11 }},
                     titlefont: {{ color: '#52514e' }}, backgroundcolor: '#fcfcfb', showbackground: true }};
        var layout = {{
            paper_bgcolor: '#fcfcfb', margin: {{ l: 0, r: 0, t: 30, b: 0 }},
            font: {{ family: 'system-ui, -apple-system, "Segoe UI", sans-serif', color: '#0b0b0b' }},
            legend: {{ orientation: 'h', x: 0, y: 1.02, font: {{ size: 13 }} }},
            hoverlabel: {{ bgcolor: '#ffffff', bordercolor: '#c3c2b7', font: {{ color: '#0b0b0b', size: 12 }}, align: 'left' }},
            scene: {{
                xaxis: Object.assign({{ title: {{ text: 'Year' }} }}, axis),
                yaxis: Object.assign({{ title: {{ text: '' }}, tickvals: D.regs.map(function (_, i) {{ return i; }}), ticktext: D.regs }}, axis),
                zaxis: Object.assign({{ title: {{ text: 'Papers, stacked by first data year' }} }}, axis),
                aspectmode: 'manual', aspectratio: {{ x: 1.6, y: 1.25, z: 0.9 }},
                camera: {{ eye: {{ x: 2.05, y: -1.8, z: 0.8 }}, center: {{ x: 0, y: 0.05, z: -0.16 }} }}
            }}
        }};
        var el = document.getElementById('landscape');
        Plotly.newPlot(el, [base].concat(traces), layout, {{ responsive: true, displaylogo: false,
            modeBarButtonsToRemove: ['toImage', 'resetCameraLastSave3d'] }});
        el.on('plotly_click', function (ev) {{
            var pt = ev.points && ev.points[0];
            if (pt && pt.data.type === 'scatter3d' && pt.customdata) window.location.href = 'index.html#' + pt.customdata;
        }});
    }})();
    </script>
"""
    out += FOOTER
    return out


if __name__ == "__main__":
    (ROOT / "index.html").write_text(build_index())
    (ROOT / "themes.html").write_text(build_themes())
    (ROOT / "variables.html").write_text(build_variables())
    (ROOT / "samples.html").write_text(build_samples())
    (ROOT / "landscape.html").write_text(build_landscape())
    print(f"built 5 pages from {len(PAPERS)} papers and {len(VARS['individual']) + len(VARS['firm'])} registers")
