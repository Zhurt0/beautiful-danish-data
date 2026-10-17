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
_SV = ROOT / "data" / "surveys.json"
SURVEYS = json.loads(_SV.read_text()) if _SV.exists() else []
SURVEYS_BY_PAPER = {}
for _s in SURVEYS:
    for _pid in _s.get("papers", []):
        SURVEYS_BY_PAPER.setdefault(_pid, []).append(_s)

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
    items = [("index.html", "Summary"), ("themes.html", "Themes"), ("samples.html", "Data & samples"), ("landscape.html", "3D data landscape"), ("codebook.html", "Codebook"), ("survey.html", "Survey"), ("variables.html", "Variable map"), ("network.html", "Author network")]
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
    if SURVEYS_BY_PAPER.get(p["id"]):
        rows.append(("Surveys", ", ".join(f'<a href="survey.html#{sv["key"]}">{e(sv["short"])}</a>' for sv in SURVEYS_BY_PAPER[p["id"]])))
    return '                    <dl class="facts">\n' + "".join(
        f'                        <div><dt>{k}</dt><dd>{v}</dd></div>\n' for k, v in rows
    ) + "                    </dl>\n"


CONCEPTS = ["Earnings and income", "Wealth, debt and consumption", "Employment and labour force status", "Hours worked",
            "Unemployment and benefits", "Retirement and pensions", "Sector and industry", "Occupation and job hierarchy",
            "Firm characteristics and productivity", "Trade and offshoring", "Education and test scores",
            "Family links, fertility and household", "Immigration and origin", "Health care use",
            "Health outcomes, diagnoses and mortality", "Crime", "Geography and neighbourhood", "Taxes and tax rates",
            "Sample definition and timing", "Other"]
SRC_LABEL = {"replication code": "replication code", "online appendix": "online appendix", "paper": "paper", "working paper": "working paper"}


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")


def def_source(d):
    loc = f" &middot; {e(d['source_location'])}" if d.get("source_location") else ""
    lab = SRC_LABEL.get(d.get("source_type"), d.get("source_type") or "source")
    if d.get("source_url"):
        return f'<a class="src" href="{e(d["source_url"])}" target="_blank" rel="noopener">{e(lab)}</a>{loc}'
    return f"{e(lab)}{loc}"


def defs_block(p):
    defs = p.get("definitions") or []
    if not defs:
        return ""
    items = ""
    for d in defs:
        codes = f'<div class="codes"><span>Codes:</span> <code>{e(d["codes"])}</code></div>' if d.get("codes") else ""
        regs = f'<div class="regs"><span>Registers:</span> {e(", ".join(d["registers"]))}</div>' if d.get("registers") else ""
        items += (f'                        <li><strong>{e(d["variable"])}</strong> <span class="concept">{e(d["concept"])}</span>'
                  f'<div>{e(d["definition"])}</div>{regs}{codes}<div class="dsrc">{def_source(d)}</div></li>\n')
    rep = ""
    if p.get("replication_package"):
        rep = f'                    <p class="rep"><a href="{e(p["replication_package"])}" target="_blank" rel="noopener">Replication package</a></p>\n'
    return (f'                    <details class="defs"><summary>How variables are defined ({len(defs)})</summary>\n'
            f'                    <ul>\n{items}                    </ul>\n{rep}                    </details>\n')


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
{facts(p)}{defs_block(p)}{themes}
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


DOMAINS = [
    ("Population and family", ["BEF — Population register", "VNDS / Residence histories"]),
    ("Income and wealth", ["IND — Income register", "FORM — Wealth register"]),
    ("Jobs and earnings", ["IDA / IDAN / IDAP — Integrated labour market database", "AKM — Labour market classification", "BFL / eIndkomst — Monthly payroll"]),
    ("Public transfers", ["DREAM — Public transfers (weekly)"]),
    ("Education", ["UDDA — Education register"]),
    ("Health, births and deaths", ["LPR — National Patient Register", "LMDB — Prescription register", "MFR — Medical Birth Register", "DOD — Death register"]),
    ("Crime", ["KRAF / KRSI — Crime registers"]),
    ("Firms and trade", ["FIRM / FIRE — Firm statistics and Accounts Statistics", "FIDA — Firm–employee link", "UHDI / UHDM — Foreign trade by firm", "VNDS / Moms — VAT-based turnover", "Company registers (CVR, ownership, management)", "Patents and R&D (external, linked by firm)"]),
    ("Surveys and other data only", []),
]
YEAR_FLOOR = 1975


def landscape_data():
    reg_to_dom = {reg: d for d, regs in DOMAINS for reg in regs}
    doms = [d for d, _ in DOMAINS]
    uses = {}
    for r in VARS["individual"] + VARS["firm"]:
        d = reg_to_dom.get(r["register"])
        for pid in r["used_by"]:
            if d and d not in uses.setdefault(pid, []):
                uses[pid].append(d)
    rows, skipped = [], []
    for p in PAPERS:
        yrs = [int(y) for y in re.findall(r"(?<!\d)(19[0-9]{2}|20[0-2][0-9])(?!\d)", p.get("period") or "")]
        yrs = [y for y in yrs if 1900 <= y <= 2026]
        if not yrs:
            skipped.append(p["id"]); continue
        tier = next(i for i, (_, g) in enumerate(TIERS) if p["group"] in g)
        ds = sorted(uses.get(p["id"]) or ["Surveys and other data only"], key=doms.index)
        rows.append(dict(id=p["id"], cite=short_cite(p), title=p["title"], journal=p["journal"],
                         period=p["period"], size=p.get("sample_size") or "not stated",
                         a=min(yrs), b=max(yrs), doms=ds, tier=tier))
    rows.sort(key=lambda r: (r["a"], r["b"], r["cite"]))
    return doms, rows, skipped


def build_landscape():
    doms, rows, skipped = landscape_data()
    early = sum(1 for r in rows if r["a"] < YEAR_FLOOR)
    out = head(
        "3D data landscape | Beautiful Danish Data",
        "A 3D view of which kinds of Danish register data each paper uses and which years its data cover, with a flat year-by-domain view underneath.",
        "landscape.html",
    )
    out += nav("landscape.html")
    payload = json.dumps(dict(doms=doms, rows=rows, tiers=[t for t, _ in TIERS], floor=YEAR_FLOOR), ensure_ascii=False)
    chips = "".join(f'<button type="button" class="chip on" data-d="{i}">{e(d)}</button>' for i, d in enumerate(doms))
    out += f"""    <section class="section intro">
        <div class="container">
            <h2 class="section-title">3D data landscape</h2>
            <p>The floor is a grid of <strong>years</strong> by <strong>data domain</strong>, shaded by how many papers use that kind of data in that year. Each paper floats above the floor at its own height, with one line for every domain it uses, running over the years its data cover. Papers are stacked by the year their data start.</p>
            <p class="note">The 20 registers are grouped into 9 domains; the <a href="variables.html">Variable map</a> lists the registers in each. {len(rows)} of {len(PAPERS)} papers have a stated data period and are shown. The time axis starts in {YEAR_FLOOR}; {early} papers with older data are drawn from {YEAR_FLOOR}, and their hover text gives the true period.</p>
        </div>
    </section>
    <section class="section viz-section">
        <div class="container">
            <div class="controls">
                <div class="ctl-row"><span class="ctl-label">Show papers using</span>{chips}<button type="button" class="chip ghost" id="all">All</button><button type="button" class="chip ghost" id="none">None</button></div>
                <div class="ctl-row"><span class="ctl-label">View</span><button type="button" class="chip view on" data-v="tilt">Oblique</button><button type="button" class="chip view" data-v="top">From above</button><button type="button" class="chip view" data-v="side">From the side</button></div>
            </div>
            <div id="landscape" class="viz" role="img" aria-label="3D chart of papers by data period and data domain"></div>
            <p class="viz-help">Drag to rotate, scroll to zoom. Hover a line to see the paper; click it to open its entry. Click a journal tier in the legend to hide it.</p>

            <h3 class="sub-title">Flat view: papers per year and domain</h3>
            <p class="blurb">The same floor as a plain grid. Click a cell to list the papers whose data cover that domain in that year.</p>
            <div id="flat" class="viz flat" role="img" aria-label="Heatmap of the number of papers by year and data domain"></div>
            <div id="cell-list" class="cell-list" aria-live="polite"></div>
        </div>
    </section>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.35.3/plotly.min.js"></script>
    <script>
    (function () {{
        var D = {payload};
        var SERIES = ['#2a78d6', '#eb6834', '#1baf7a'];
        var RAMP = [[0, '#f4f8fd'], [0.0001, '#cde2fb'], [0.3, '#86b6ef'], [0.6, '#3987e5'], [0.85, '#1c5cab'], [1, '#0d366b']];
        var FONT = {{ family: 'system-ui, -apple-system, "Segoe UI", sans-serif', color: '#0b0b0b' }};
        var HOVER = {{ bgcolor: '#ffffff', bordercolor: '#c3c2b7', font: {{ color: '#0b0b0b', size: 12 }}, align: 'left' }};
        var on = D.doms.map(function () {{ return true; }});
        var y1 = 0; D.rows.forEach(function (r) {{ y1 = Math.max(y1, r.b); }});
        var y0 = D.floor;
        var years = []; for (var y = y0; y <= y1; y++) years.push(y);

        function visibleRows() {{
            return D.rows.filter(function (r) {{ return r.doms.some(function (d) {{ return on[D.doms.indexOf(d)]; }}); }});
        }}
        function counts(rows) {{
            var c = D.doms.map(function () {{ return years.map(function () {{ return 0; }}); }});
            rows.forEach(function (r) {{
                r.doms.forEach(function (d) {{
                    var i = D.doms.indexOf(d);
                    for (var yr = Math.max(r.a, y0); yr <= r.b; yr++) c[i][yr - y0] += 1;
                }});
            }});
            return c;
        }}

        function floorTrace(c) {{
            // blocky floor: each cell is a flat tile with a small gap between domains
            var xs = [], ys = [], zs = [], sc = [];
            years.forEach(function (yr) {{ xs.push(yr - 0.5, yr + 0.5); }});
            D.doms.forEach(function (_, i) {{ ys.push(i - 0.42, i + 0.42); }});
            ys.forEach(function (_, j) {{
                var di = Math.floor(j / 2), zr = [], sr = [];
                xs.forEach(function (_, k) {{ zr.push(0); sr.push(c[di][Math.floor(k / 2)]); }});
                zs.push(zr); sc.push(sr);
            }});
            return {{ type: 'surface', x: xs, y: ys, z: zs, surfacecolor: sc, colorscale: RAMP, cmin: 0, showlegend: false,
                     colorbar: {{ title: {{ text: 'Papers', font: {{ size: 12 }} }}, thickness: 12, len: 0.5, x: 1.0, tickfont: {{ size: 11 }} }},
                     hoverinfo: 'skip', lighting: {{ ambient: 1, diffuse: 0, specular: 0 }},
                     contours: {{ x: {{ show: false }}, y: {{ show: false }}, z: {{ show: false }} }} }};
        }}

        function paperTraces(rows) {{
            var tr = D.tiers.map(function (name, t) {{
                return {{ type: 'scatter3d', mode: 'lines', name: name, x: [], y: [], z: [], text: [], customdata: [],
                         line: {{ color: SERIES[t], width: 6 }}, hovertemplate: '%{{text}}<extra></extra>' }};
            }});
            rows.forEach(function (r, k) {{
                var t = tr[r.tier], z = k + 1;
                var label = '<b>' + r.cite + '</b><br>' + r.title + '<br>' + r.journal +
                            '<br>Data period: ' + r.period + '<br>Sample: ' + r.size;
                r.doms.forEach(function (d) {{
                    if (!on[D.doms.indexOf(d)]) return;
                    var yi = D.doms.indexOf(d);
                    for (var yr = Math.max(r.a, y0); yr <= r.b; yr++) {{
                        t.x.push(yr); t.y.push(yi); t.z.push(z); t.text.push(label + '<br>Domain: ' + d); t.customdata.push(r.id);
                    }}
                    t.x.push(null); t.y.push(null); t.z.push(null); t.text.push(null); t.customdata.push(null);
                }});
            }});
            return tr;
        }}

        var CAMS = {{
            tilt: {{ eye: {{ x: 1.25, y: -1.55, z: 1.05 }}, center: {{ x: 0, y: 0, z: -0.15 }}, up: {{ x: 0, y: 0, z: 1 }} }},
            top:  {{ eye: {{ x: 0, y: -0.0001, z: 2.4 }}, center: {{ x: 0, y: 0, z: 0 }}, up: {{ x: 0, y: 1, z: 0 }} }},
            side: {{ eye: {{ x: 0, y: -2.4, z: 0.05 }}, center: {{ x: 0, y: 0, z: 0 }}, up: {{ x: 0, y: 0, z: 1 }} }}
        }};
        var view = 'tilt';
        function axis(extra) {{
            return Object.assign({{ gridcolor: '#e1e0d9', zerolinecolor: '#c3c2b7', linecolor: '#c3c2b7', showbackground: true,
                backgroundcolor: '#fcfcfb', tickfont: {{ color: '#52514e', size: 11 }}, title: {{ font: {{ color: '#52514e', size: 12 }} }} }}, extra);
        }}
        function layout(n) {{
            var cam = JSON.parse(JSON.stringify(CAMS[view])); cam.projection = {{ type: 'orthographic' }};
            return {{
                paper_bgcolor: '#fcfcfb', font: FONT, hoverlabel: HOVER, margin: {{ l: 0, r: 0, t: 36, b: 0 }},
                legend: {{ orientation: 'h', x: 0, y: 1.04, font: {{ size: 13 }} }},
                uirevision: view,
                scene: {{
                    xaxis: axis({{ title: {{ text: 'Year' }}, range: [y0 - 0.5, y1 + 0.5], dtick: 5 }}),
                    yaxis: axis({{ title: {{ text: '' }}, tickvals: D.doms.map(function (_, i) {{ return i; }}), ticktext: D.doms, range: [-0.6, D.doms.length - 0.4] }}),
                    zaxis: axis({{ title: {{ text: 'Papers (stacked by first data year)' }}, range: [0, Math.max(n, 1) + 2] }}),
                    aspectmode: 'manual', aspectratio: {{ x: 1.7, y: 1.1, z: 1.15 }},
                    camera: cam
                }}
            }};
        }}

        var el = document.getElementById('landscape');
        function draw() {{
            var rows = visibleRows();
            Plotly.react(el, [floorTrace(counts(rows))].concat(paperTraces(rows)), layout(rows.length),
                {{ responsive: true, displaylogo: false, modeBarButtonsToRemove: ['toImage', 'resetCameraLastSave3d'] }});
            drawFlat(rows);
        }}

        var flat = document.getElementById('flat');
        var list = document.getElementById('cell-list');
        var flatRows = [];
        function drawFlat(rows) {{
            flatRows = rows;
            var c = counts(rows);
            Plotly.react(flat, [{{
                type: 'heatmap', x: years, y: D.doms, z: c, colorscale: RAMP, zmin: 0, xgap: 1, ygap: 3,
                colorbar: {{ title: {{ text: 'Papers', font: {{ size: 12 }} }}, thickness: 12, tickfont: {{ size: 11 }} }},
                hovertemplate: '%{{y}}, %{{x}}: %{{z}} papers<extra></extra>'
            }}], {{
                paper_bgcolor: '#fcfcfb', plot_bgcolor: '#fcfcfb', font: FONT, hoverlabel: HOVER,
                margin: {{ l: 190, r: 10, t: 10, b: 40 }},
                xaxis: {{ dtick: 5, tickfont: {{ color: '#52514e', size: 11 }}, showgrid: false }},
                yaxis: {{ autorange: 'reversed', tickfont: {{ color: '#52514e', size: 12 }}, showgrid: false }}
            }}, {{ responsive: true, displayModeBar: false }});
        }}
        function esc(s) {{ return String(s).replace(/[&<>"]/g, function (ch) {{ return {{ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }}[ch]; }}); }}

        draw();
        el.on('plotly_click', function (ev) {{
            var pt = ev.points && ev.points[0];
            if (pt && pt.data.type === 'scatter3d' && pt.customdata) window.location.href = 'index.html#' + pt.customdata;
        }});
        flat.on('plotly_click', function (ev) {{
            var pt = ev.points && ev.points[0]; if (!pt) return;
            var yr = pt.x, dom = pt.y;
            var hits = flatRows.filter(function (r) {{ return r.doms.indexOf(dom) !== -1 && r.a <= yr && r.b >= yr; }});
            list.innerHTML = '<h4>' + esc(dom) + ', ' + yr + ': ' + hits.length + ' papers</h4><ul>' + hits.map(function (r) {{
                return '<li><span class="sw" style="background:' + SERIES[r.tier] + '"></span><a href="index.html#' + r.id + '">' + esc(r.cite) + '</a> ' + esc(r.title) +
                       ' <span class="muted">(' + esc(r.period) + ')</span></li>';
            }}).join('') + '</ul>';
        }});

        Array.prototype.forEach.call(document.querySelectorAll('.chip[data-d]'), function (b) {{
            b.addEventListener('click', function () {{
                var i = +b.getAttribute('data-d'); on[i] = !on[i]; b.classList.toggle('on', on[i]); draw();
            }});
        }});
        function setAll(v) {{
            on = on.map(function () {{ return v; }});
            Array.prototype.forEach.call(document.querySelectorAll('.chip[data-d]'), function (b) {{ b.classList.toggle('on', v); }});
            draw();
        }}
        document.getElementById('all').addEventListener('click', function () {{ setAll(true); }});
        document.getElementById('none').addEventListener('click', function () {{ setAll(false); }});
        Array.prototype.forEach.call(document.querySelectorAll('.chip.view'), function (b) {{
            b.addEventListener('click', function () {{
                view = b.getAttribute('data-v');
                Array.prototype.forEach.call(document.querySelectorAll('.chip.view'), function (x) {{ x.classList.toggle('on', x === b); }});
                draw();
            }});
        }});
    }})();
    </script>
"""
    out += FOOTER
    return out


def build_codebook():
    out = head(
        "Codebook | Beautiful Danish Data",
        "How papers using Danish register data define their variables: GP visits, public-sector employment, earnings, hours, mass layoffs and more, with register variable names, codes and sources.",
        "codebook.html",
    )
    out += nav("codebook.html")
    entries = []
    for p in PAPERS:
        for d in p.get("definitions") or []:
            entries.append((d, p))
    n_papers = sum(1 for p in PAPERS if p.get("definitions"))
    by_src = {}
    for d, _ in entries:
        by_src[d.get("source_type")] = by_src.get(d.get("source_type"), 0) + 1
    present = [c for c in CONCEPTS if any(d["concept"] == c for d, _ in entries)]
    chips = "".join(f'<button type="button" class="chip" data-c="{slug(c)}">{e(c)}</button>' for c in present)
    out += f"""    <section class="section intro">
        <div class="container">
            <h2 class="section-title">Codebook</h2>
            <p>How each paper builds the variables it uses: the rule, the threshold, the register and, where the authors state them, the exact register variable names and code values. Definitions come from replication code where it is public, otherwise from online appendices, working-paper appendices or the paper itself, and each one links to its source.</p>
            <p class="note">{len(entries)} definitions from {n_papers} papers. By source: {", ".join(f"{v} from {k}" for k, v in sorted(by_src.items(), key=lambda kv: -kv[1]))}. Register variable names and codes change between years and projects, so check the current Statistics Denmark documentation before reusing a code list. AEA replication packages sit on openICPSR, which could not be read for this page, so AEA papers rely on their appendices.</p>
        </div>
    </section>
    <section class="section">
        <div class="container">
            <input id="cfilter" class="filter" type="search" placeholder="Search variables, codes or registers, e.g. GP, SOCIO13, public sector" aria-label="Search the codebook">
            <div class="ctl-row cb-chips"><span class="ctl-label">Concept</span>{chips}<button type="button" class="chip ghost" id="call">All</button></div>
"""
    for c in present:
        rows = sorted([(d, p) for d, p in entries if d["concept"] == c], key=lambda dp: (dp[0]["variable"].lower(), -dp[1]["year"]))
        out += f"""            <div class="cb-group" data-c="{slug(c)}">
            <h3 class="cb-title" id="{slug(c)}">{e(c)} <span>{len(rows)}</span></h3>
            <div class="table-wrap">
            <table class="codebook">
                <thead><tr><th>Variable</th><th>Paper</th><th>Definition</th><th>Registers and codes</th><th>Source</th></tr></thead>
                <tbody>
"""
        for d, p in rows:
            regs = e(", ".join(d.get("registers") or []))
            codes = f'<br><code>{e(d["codes"])}</code>' if d.get("codes") else ""
            out += (f'                    <tr><td data-label="Variable"><strong>{e(d["variable"])}</strong></td>'
                    f'<td data-label="Paper"><a href="index.html#{p["id"]}">{e(short_cite(p))}</a></td>'
                    f'<td data-label="Definition">{e(d["definition"])}</td>'
                    f'<td data-label="Registers and codes">{regs}{codes}</td>'
                    f'<td data-label="Source">{def_source(d)}</td></tr>\n')
        out += """                </tbody>
            </table>
            </div>
            </div>
"""
    out += """        </div>
    </section>
    <script>
    (function () {
        var groups = Array.prototype.slice.call(document.querySelectorAll('.cb-group'));
        var chips = Array.prototype.slice.call(document.querySelectorAll('.cb-chips .chip[data-c]'));
        var active = null;
        function apply() {
            var q = document.getElementById('cfilter').value.toLowerCase();
            groups.forEach(function (g) {
                var show = !active || g.getAttribute('data-c') === active, n = 0;
                Array.prototype.forEach.call(g.querySelectorAll('tbody tr'), function (r) {
                    var hit = show && (!q || r.innerText.toLowerCase().indexOf(q) !== -1);
                    r.style.display = hit ? '' : 'none'; if (hit) n++;
                });
                g.style.display = n ? '' : 'none';
            });
        }
        chips.forEach(function (b) {
            b.addEventListener('click', function () {
                active = active === b.getAttribute('data-c') ? null : b.getAttribute('data-c');
                chips.forEach(function (x) { x.classList.toggle('on', x.getAttribute('data-c') === active); });
                apply();
            });
        });
        document.getElementById('call').addEventListener('click', function () {
            active = null; chips.forEach(function (x) { x.classList.remove('on'); }); apply();
        });
        document.getElementById('cfilter').addEventListener('input', apply);
    })();
    </script>
"""
    out += FOOTER
    return out


def build_survey():
    out = head(
        "Survey | Beautiful Danish Data",
        "Questionnaires behind the surveys that papers in Beautiful Danish Data link to Danish registers: Labour Force Survey, Expenditure Survey, DALSC, SHARE, election studies and the authors' own surveys.",
        "survey.html",
    )
    out += nav("survey.html")
    by_id = {p["id"]: p for p in PAPERS}
    QT = ("questionnaire", "appendix with questions", "codebook", "questions quoted in paper")
    n_docs = sum(1 for sv in SURVEYS for d in sv.get("documents", []) if d.get("type") in QT)
    with_q = sum(1 for sv in SURVEYS if any(d.get("type") in QT for d in sv.get("documents", [])))
    out += f"""    <section class="section intro">
        <div class="container">
            <h2 class="section-title">Survey</h2>
            <p>Many papers link register data to a survey through the personal identifier: the Labour Force Survey for hours and occupations, the Expenditure Survey to validate imputed consumption, children's cohort surveys, election studies, or a survey the authors fielded themselves. This page collects the questionnaires behind those surveys, so you can see exactly what respondents were asked.</p>
            <p class="note">{len(SURVEYS)} surveys used by {len({pid for sv in SURVEYS for pid in sv.get("papers", [])})} papers; {with_q} have question wording online: a full questionnaire, a codebook with the questions, an appendix listing them, or at least the questions quoted in the paper ({n_docs} documents in all). Every document was opened and checked before it was listed. Statistics Denmark documents are also mirrored here, because its <a href="https://www.dst.dk/da/presse/kildeangivelse" target="_blank" rel="noopener">terms</a> allow free copying with the source credited. Each copy was checked before mirroring (a genuine PDF served from dst.dk, no embedded files, scripts or forms) and shows its SHA-256 checksum. SHARE questionnaires are linked rather than copied, because SHARE-ERIC holds the rights and its conditions of use grant no right to republish them; other documents link to their publishers. The microdata themselves are confidential and accessed through Statistics Denmark or the survey owner.</p>
        </div>
    </section>
    <section class="section">
        <div class="container">
            <input id="sfilter" class="filter" type="search" placeholder="Filter surveys, e.g. labour force, children, SHARE, Kreiner" aria-label="Filter surveys">
"""
    groups = [("Official and academic surveys", [sv for sv in SURVEYS if not sv.get("custom")]),
              ("Surveys and experiments fielded by the authors", [sv for sv in SURVEYS if sv.get("custom")])]
    TYPE_LABEL = {"questionnaire": "Questionnaire", "codebook": "Codebook", "appendix with questions": "Questions in appendix", "questions quoted in paper": "Questions quoted in paper", "documentation": "Documentation"}
    for gname, items in groups:
        if not items:
            continue
        out += f'            <h3 class="cb-title">{e(gname)} <span>{len(items)}</span></h3>\n'
        for sv in items:
            papers = ", ".join(f'<a href="index.html#{pid}">{e(short_cite(by_id[pid]))}</a>' for pid in sv.get("papers", []) if pid in by_id)
            docs = ""
            for d in sv.get("documents", []):
                meta = " &middot; ".join(e(str(x)) for x in [d.get("language"), d.get("wave"), (f'{d["pages"]} pages' if d.get("pages") else None), d.get("location")] if x)
                mirror = ""
                if d.get("mirror"):
                    m = d["mirror"]
                    mirror = (f'<div class="mirror"><a href="{e(m["path"])}" download>Download copy (PDF, {m["pages"]} pages, {m["bytes"] / 1e6:.1f} MB)</a>'
                              f' &middot; Source: {e(m["source"])}, <a href="{e(d["url"])}" target="_blank" rel="noopener">original</a>, retrieved {e(m["retrieved"])}'
                              f' &middot; <span class="sha" title="SHA-256 {e(m["sha256"])}">sha256 {e(m["sha256"][:12])}&hellip;</span></div>')
                docs += (f'<li><span class="dtype t-{slug(d.get("type") or "doc")}">{e(TYPE_LABEL.get(d.get("type"), d.get("type") or "Document"))}</span> '
                         f'<a href="{e(d["url"])}" target="_blank" rel="noopener">{e(d["title"])}</a>'
                         f'{" <span class=muted>" + meta + "</span>" if meta else ""}{mirror}</li>')
            docs_html = f"<ul class=\"docs\">{docs}</ul>" if docs else '<p class="na">No questionnaire found online.</p>'
            landing = f' &middot; <a href="{e(sv["landing_page"])}" target="_blank" rel="noopener">Survey home page</a>' if sv.get("landing_page") else ""
            extra = ""
            if sv.get("access"):
                extra += f'<p class="sv-meta"><strong>Access:</strong> {e(sv["access"])}</p>'
            if sv.get("notes"):
                extra += f'<p class="sv-meta muted">{e(sv["notes"])}</p>'
            out += f"""            <article class="survey" id="{e(sv['key'])}">
                <h4>{e(sv['name'])}</h4>
                <p class="meta">{e(sv.get('owner') or '')}{landing}</p>
                <p class="summary">{e(sv.get('description') or '')}</p>
                <p class="sv-meta"><strong>Used by:</strong> {papers} &middot; <strong>Waves used:</strong> {e(sv.get('waves_used') or 'not stated')}</p>
                {docs_html}
                {extra}
            </article>
"""
    out += """        </div>
    </section>
    <script>
    document.getElementById('sfilter').addEventListener('input', function () {
        var q = this.value.toLowerCase();
        Array.prototype.forEach.call(document.querySelectorAll('article.survey'), function (a) {
            a.style.display = a.innerText.toLowerCase().indexOf(q) === -1 ? 'none' : '';
        });
    });
    </script>
"""
    out += FOOTER
    return out


_NW = ROOT / "data" / "network.json"
NETWORK = json.loads(_NW.read_text()) if _NW.exists() else None
NET_GROUPS = [("Danish universities", "#2a78d6"), ("Other Danish institutions", "#eb6834"),
              ("Institutions abroad", "#1baf7a"), ("Not listed", "#a9a8a0")]

NETWORK_JS = r"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
    <script>
    (function () {
        var D = __DATA__;
        var COLOR = {}; D.groups.forEach(function (g) { COLOR[g[0]] = g[1]; });
        var nodes = D.nodes.map(function (n, i) { return Object.assign({ i: i }, n); });
        var links = D.links.map(function (l) { return { source: l[0], target: l[1], w: l[2], p: l[3] }; });
        var adj = nodes.map(function () { return []; });
        links.forEach(function (l) { adj[l.source].push([l.target, l.w, l.p]); adj[l.target].push([l.source, l.w, l.p]); });
        function r(n) { return 3 + 2.4 * Math.sqrt(n.papers.length); }

        var sim = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).distance(function (l) { return 30 + 14 / l.w; }).strength(0.6))
            .force('charge', d3.forceManyBody().strength(-70))
            .force('collide', d3.forceCollide(function (n) { return r(n) + 1.5; }))
            .force('x', d3.forceX(0).strength(0.07))
            .force('y', d3.forceY(0).strength(0.07))
            .stop();
        for (var t = 0; t < 420; t++) sim.tick();

        var box = document.getElementById('net');
        var W = box.clientWidth, H = box.clientHeight;
        var svg = d3.select(box).append('svg').attr('width', W).attr('height', H).attr('viewBox', [0, 0, W, H]);
        var g = svg.append('g');
        var link = g.append('g').attr('stroke', '#c3c2b7').attr('stroke-linecap', 'round').selectAll('line').data(links).join('line')
            .attr('x1', function (l) { return l.source.x; }).attr('y1', function (l) { return l.source.y; })
            .attr('x2', function (l) { return l.target.x; }).attr('y2', function (l) { return l.target.y; })
            .attr('stroke-width', function (l) { return 0.8 + 1.1 * (l.w - 1); }).attr('stroke-opacity', 0.75);
        var node = g.append('g').selectAll('circle').data(nodes).join('circle')
            .attr('cx', function (n) { return n.x; }).attr('cy', function (n) { return n.y; }).attr('r', r)
            .attr('fill', function (n) { return COLOR[n.group]; }).attr('stroke', '#fcfcfb').attr('stroke-width', 1)
            .style('cursor', 'pointer');
        var labelG = g.append('g').attr('class', 'net-labels');
        var kc = 1, near = null, focusI = null;
        // name authors at a constant on-screen size, most prolific first, skipping any label that would overlap one already placed
        function labels() {
            var cand = near ? nodes.filter(function (n) { return near[n.i]; }) : nodes.filter(function (n) { return n.papers.length >= 3; });
            cand.sort(function (a, b) { return (b.i === focusI) - (a.i === focusI) || b.papers.length - a.papers.length || adj[b.i].length - adj[a.i].length; });
            var placed = [], fs = 11 / kc;
            var keep = cand.filter(function (n) {
                var x = n.x + r(n) + 2 / kc, bx = [x, n.y - 0.6 * fs, x + 0.58 * fs * n.name.length, n.y + 0.6 * fs];
                var hit = placed.some(function (q) { return bx[0] < q[2] && bx[2] > q[0] && bx[1] < q[3] && bx[3] > q[1]; });
                if (!hit) placed.push(bx);
                return !hit;
            });
            labelG.style('font-size', fs + 'px').style('stroke-width', (3 / kc) + 'px');
            labelG.selectAll('text').data(keep, function (n) { return n.i; }).join('text')
                .attr('x', function (n) { return n.x + r(n) + 2 / kc; }).attr('y', function (n) { return n.y + 0.35 * fs; })
                .attr('font-weight', function (n) { return n.i === focusI ? 700 : 400; })
                .text(function (n) { return n.name; });
        }

        var zoom = d3.zoom().scaleExtent([0.3, 8])
            .on('zoom', function (ev) {
                g.attr('transform', ev.transform);
                labelG.style('font-size', (11 / ev.transform.k) + 'px').style('stroke-width', (3 / ev.transform.k) + 'px');
            })
            .on('end', function (ev) { kc = ev.transform.k; labels(); });
        function fit(list, ms) {
            // leave room on the right for the names
            var a0 = d3.min(list, function (n) { return n.x - r(n); }), a1 = d3.max(list, function (n) { return n.x + r(n); });
            var b0 = d3.min(list, function (n) { return n.y - r(n); }), b1 = d3.max(list, function (n) { return n.y + r(n); });
            var pad = Math.min(130, W * 0.25);
            var s = Math.min(2.4, Math.min((W - pad - 20) / Math.max(a1 - a0, 1), (H - 30) / Math.max(b1 - b0, 1)));
            var tr = d3.zoomIdentity.translate((W - pad) / 2, H / 2).scale(s).translate(-(a0 + a1) / 2, -(b0 + b1) / 2);
            if (ms) svg.transition().duration(ms).call(zoom.transform, tr); else svg.call(zoom.transform, tr);
        }
        svg.call(zoom);
        fit(nodes, 0);

        var tip = d3.select(box).append('div').attr('class', 'net-tip').style('display', 'none');
        var selected = null, inst = '';
        function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
        function paint(focus) {
            near = null; focusI = focus;
            if (focus !== null) { near = {}; near[focus] = 1; adj[focus].forEach(function (a) { near[a[0]] = 1; }); }
            node.attr('opacity', function (n) {
                if (near) return near[n.i] ? 1 : 0.12;
                if (inst) return n.institutions.indexOf(inst) >= 0 ? 1 : 0.12;
                return 1;
            }).attr('stroke', function (n) { return n.i === focus ? '#0b0b0b' : '#fcfcfb'; }).attr('stroke-width', function (n) { return n.i === focus ? 2 : 1; });
            link.attr('stroke-opacity', function (l) {
                if (near) return (l.source.i === focus || l.target.i === focus) ? 0.95 : 0.06;
                if (inst) return (l.source.institutions.indexOf(inst) >= 0 && l.target.institutions.indexOf(inst) >= 0) ? 0.9 : 0.06;
                return 0.75;
            }).attr('stroke', function (l) { return near && (l.source.i === focus || l.target.i === focus) ? '#52514e' : '#c3c2b7'; });
            labels();
            labelG.selectAll('text').attr('opacity', function (n) { return inst && !near && n.institutions.indexOf(inst) < 0 ? 0.15 : 1; });
        }
        function show(i, zoomTo) {
            selected = i;
            paint(i);
            if (zoomTo) fit(nodes.filter(function (n) { return near[n.i]; }), 500);
            var n = nodes[i], panel = document.getElementById('net-panel');
            var co = adj[i].slice().sort(function (a, b) { return b[1] - a[1] || nodes[a[0]].name.localeCompare(nodes[b[0]].name); });
            var h = '<h3>' + esc(n.name) + '</h3>';
            h += '<p class="np-aff"><span class="sw" style="background:' + COLOR[n.group] + '"></span>' + (n.primary.length ? esc(n.primary.join('; ')) : 'Affiliation not listed') + '</p>';
            if (n.institutions.length > n.primary.length) h += '<p class="np-sub">All affiliations on these papers: ' + esc(n.institutions.join('; ')) + '</p>';
            h += '<h4>' + n.papers.length + (n.papers.length === 1 ? ' paper' : ' papers') + '</h4><ul>';
            n.papers.forEach(function (pid) { var p = D.papers[pid]; h += '<li><a href="index.html#' + pid + '">' + esc(p.cite) + '</a>, <em>' + esc(p.title) + '</em></li>'; });
            h += '</ul><h4>' + co.length + (co.length === 1 ? ' co-author' : ' co-authors') + '</h4>';
            if (co.length) {
                h += '<ul class="np-co">';
                co.forEach(function (a) { h += '<li><button type="button" class="linkish" data-i="' + a[0] + '">' + esc(nodes[a[0]].name) + '</button>' + (a[1] > 1 ? ' <span class="muted">(' + a[1] + ' papers)</span>' : '') + '</li>'; });
                h += '</ul>';
            } else h += '<p class="muted">Sole author of every paper listed here.</p>';
            h += '<p class="np-sub"><a href="' + n.openalex + '" target="_blank" rel="noopener">OpenAlex profile</a></p>';
            panel.innerHTML = h;
        }
        function clear() {
            selected = null; paint(null);
            document.getElementById('net-panel').innerHTML = document.getElementById('net-panel-default').innerHTML;
        }
        node.on('mouseenter', function (ev, n) {
            if (selected === null) paint(n.i);
            tip.style('display', 'block').html('<strong>' + esc(n.name) + '</strong><br>' + (n.primary.length ? esc(n.primary[0]) : 'Affiliation not listed') + '<br>' + n.papers.length + (n.papers.length === 1 ? ' paper' : ' papers') + ', ' + adj[n.i].length + ' co-authors');
        }).on('mousemove', function (ev) {
            var p = d3.pointer(ev, box);
            tip.style('left', Math.min(p[0] + 14, W - 240) + 'px').style('top', (p[1] + 14) + 'px');
        }).on('mouseleave', function () {
            tip.style('display', 'none');
            if (selected === null) paint(null);
        }).on('click', function (ev, n) { ev.stopPropagation(); show(n.i); });
        svg.on('click', function () { if (selected !== null) clear(); });

        document.addEventListener('click', function (ev) {
            var b = ev.target.closest('[data-i]');
            if (!b) return;
            ev.preventDefault();
            show(+b.getAttribute('data-i'), true);
            if (!b.closest('#net-panel')) box.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });
        var search = document.getElementById('net-search');
        search.addEventListener('change', function () {
            var q = search.value.trim().toLowerCase();
            var hit = nodes.filter(function (n) { return n.name.toLowerCase() === q; })[0] || nodes.filter(function (n) { return n.name.toLowerCase().indexOf(q) >= 0; })[0];
            if (q && hit) show(hit.i, true);
        });
        var sel = document.getElementById('net-inst');
        sel.addEventListener('change', function () { inst = sel.value; if (selected !== null) clear(); else paint(null); });
        document.getElementById('net-reset').addEventListener('click', function () {
            inst = ''; sel.value = ''; search.value = ''; clear();
            fit(nodes, 400);
        });

        clear();

        document.querySelectorAll('table.net-sort').forEach(function (table) {
            var body = table.tBodies[0], rows = Array.prototype.slice.call(body.rows), dir = {};
            Array.prototype.forEach.call(table.tHead.rows[0].cells, function (th, c) {
                th.addEventListener('click', function () {
                    dir[c] = !dir[c];
                    rows.sort(function (a, b) {
                        var ka = a.cells[c].getAttribute('data-v') || a.cells[c].innerText.trim().toLowerCase();
                        var kb = b.cells[c].getAttribute('data-v') || b.cells[c].innerText.trim().toLowerCase();
                        if (!isNaN(ka) && !isNaN(kb)) { ka = +ka; kb = +kb; }
                        return (ka < kb ? -1 : ka > kb ? 1 : 0) * (dir[c] ? 1 : -1);
                    });
                    rows.forEach(function (row) { body.appendChild(row); });
                });
            });
        });
    })();
    </script>
"""


def build_network():
    nw = NETWORK
    idx = {n["id"]: i for i, n in enumerate(nw["nodes"])}
    nodes = nw["nodes"]
    deg = [0] * len(nodes)
    for l in nw["links"]:
        deg[idx[l["source"]]] += 1
        deg[idx[l["target"]]] += 1
    cnt = {g: sum(1 for n in nodes if n["group"] == g) for g, _ in NET_GROUPS}
    # institutions: authors who list it on any paper, and the papers they wrote while listing it
    inst = {}
    for i, n in enumerate(nodes):
        for name in n["institutions"]:
            inst.setdefault(name, set()).add(i)
    inst_papers = {k: {pid for i in v for pid in nodes[i]["papers"]} for k, v in inst.items()}
    inst_rows = sorted(inst, key=lambda k: (-len(inst[k]), -len(inst_papers[k]), k))
    # connected components
    parent = list(range(len(nodes)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for l in nw["links"]:
        parent[find(idx[l["source"]])] = find(idx[l["target"]])
    comp = {}
    for i in range(len(nodes)):
        comp[find(i)] = comp.get(find(i), 0) + 1
    biggest = max(comp.values())
    solo = sum(1 for d in deg if d == 0)

    out = head(
        "Author network | Beautiful Danish Data",
        "Who has written with whom among the authors of papers using Danish administrative data, and where they were based.",
        "network.html",
    )
    out += nav("network.html")
    legend = "".join(f'<span class="lg"><span class="sw" style="background:{c}"></span>{e(g)} <span class="muted">({cnt[g]})</span></span>' for g, c in NET_GROUPS)
    opts = "".join(f'<option value="{e(k)}">{e(k)} ({len(inst[k])})</option>' for k in inst_rows if len(inst[k]) >= 2)
    names = "".join(f'<option value="{e(n["name"])}"></option>' for n in sorted(nodes, key=lambda n: n["name"]))
    out += f"""    <section class="section intro">
        <div class="container">
            <h2 class="section-title">Author network</h2>
            <p>Every author of the {len(PAPERS)} papers, linked to everyone they wrote one of these papers with. {len(nodes)} authors and {len(nw["links"])} co-author pairs. {biggest} authors are joined in one connected group; {solo} wrote all their papers here alone.</p>
            <p class="note">Affiliations are those printed on each paper, taken from OpenAlex. Colour shows where an author was based on most of their papers here. Research networks such as NBER, CEPR, IZA and CESifo are left out, since nearly everyone lists one. Names were matched by OpenAlex author ID and checked by hand for duplicates.</p>
        </div>
    </section>
    <section class="section viz-section">
        <div class="container">
            <div class="controls">
                <div class="ctl-row net-legend">{legend}</div>
                <div class="ctl-row"><span class="ctl-label">Find an author</span><input id="net-search" class="net-input" list="net-names" placeholder="Type a name" aria-label="Find an author"><datalist id="net-names">{names}</datalist>
                <span class="ctl-label">Highlight an institution</span><select id="net-inst" class="net-input" aria-label="Highlight an institution"><option value="">All institutions</option>{opts}</select>
                <button type="button" class="chip ghost" id="net-reset">Reset</button></div>
            </div>
            <div class="net-wrap">
                <div id="net" class="viz net" role="img" aria-label="Network of co-authors. The tables below list the same authors, institutions and pairs."></div>
                <aside id="net-panel" class="net-panel" aria-live="polite"></aside>
            </div>
            <template id="net-panel-default"><h3>Click an author</h3><p class="muted">Circle size is the number of papers; line width is the number of papers a pair wrote together. Most authors with three or more papers are named; the rest show their name on hover. Hover to see an author's co-authors, click to list their papers and affiliations, drag to pan and scroll to zoom.</p></template>
            <p class="viz-help">The same information is in the tables below.</p>

            <h3 class="sub-title">Pairs who wrote the most papers together</h3>
            <div class="table-wrap"><table class="net-sort">
                <thead><tr><th>Authors</th><th>Joint papers</th><th>Papers</th></tr></thead>
                <tbody>
"""
    pairs = sorted(nw["links"], key=lambda l: (-l["weight"], nodes[idx[l["source"]]]["name"]))
    for l in [x for x in pairs if x["weight"] >= 2]:
        a, b = idx[l["source"]], idx[l["target"]]
        ps = "; ".join(f'<a href="index.html#{pid}">{e(nw["papers"][pid]["cite"])}</a>' for pid in l["papers"])
        out += (f'                    <tr><td><a href="#net" data-i="{a}">{e(nodes[a]["name"])}</a> &amp; <a href="#net" data-i="{b}">{e(nodes[b]["name"])}</a></td>'
                f'<td data-v="{l["weight"]}">{l["weight"]}</td><td>{ps}</td></tr>\n')
    out += f"""                </tbody>
            </table></div>

            <h3 class="sub-title">Institutions</h3>
            <p class="blurb">Institutions listed by at least two authors, with the number of authors who list them and the papers those authors wrote. Click a column to sort.</p>
            <div class="table-wrap"><table class="net-sort">
                <thead><tr><th>Institution</th><th>Authors</th><th>Papers</th></tr></thead>
                <tbody>
"""
    for k in [x for x in inst_rows if len(inst[x]) >= 2]:
        out += f'                    <tr><td>{e(k)}</td><td data-v="{len(inst[k])}">{len(inst[k])}</td><td data-v="{len(inst_papers[k])}">{len(inst_papers[k])}</td></tr>\n'
    out += f"""                </tbody>
            </table></div>

            <details class="net-all">
                <summary>All {len(nodes)} authors</summary>
                <div class="table-wrap"><table class="net-sort">
                    <thead><tr><th>Author</th><th>Papers</th><th>Co-authors</th><th>Affiliations</th></tr></thead>
                    <tbody>
"""
    order = sorted(range(len(nodes)), key=lambda i: (-len(nodes[i]["papers"]), -deg[i], nodes[i]["name"]))
    for i in order:
        n = nodes[i]
        aff = e("; ".join(n["institutions"])) if n["institutions"] else '<span class="muted">Not listed</span>'
        out += (f'                        <tr><td><a href="#net" data-i="{i}">{e(n["name"])}</a></td><td data-v="{len(n["papers"])}">{len(n["papers"])}</td>'
                f'<td data-v="{deg[i]}">{deg[i]}</td><td>{aff}</td></tr>\n')
    out += """                    </tbody>
                </table></div>
            </details>
        </div>
    </section>
"""
    payload = dict(groups=NET_GROUPS, papers=nw["papers"],
                   nodes=[dict(name=n["name"], papers=n["papers"], primary=n["primary"], group=n["group"],
                               institutions=n["institutions"], openalex=n["openalex"]) for n in nodes],
                   links=[[idx[l["source"]], idx[l["target"]], l["weight"], l["papers"]] for l in nw["links"]])
    out += NETWORK_JS.replace("__DATA__", json.dumps(payload, ensure_ascii=False).replace("</", "<\\/"))
    out += FOOTER
    return out


if __name__ == "__main__":
    (ROOT / "index.html").write_text(build_index())
    (ROOT / "themes.html").write_text(build_themes())
    (ROOT / "variables.html").write_text(build_variables())
    (ROOT / "samples.html").write_text(build_samples())
    (ROOT / "landscape.html").write_text(build_landscape())
    (ROOT / "codebook.html").write_text(build_codebook())
    (ROOT / "survey.html").write_text(build_survey())
    pages = 7
    if NETWORK:
        (ROOT / "network.html").write_text(build_network())
        pages += 1
    print(f"built {pages} pages from {len(PAPERS)} papers and {len(VARS['individual']) + len(VARS['firm'])} registers")
