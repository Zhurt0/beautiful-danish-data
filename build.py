#!/usr/bin/env python3
"""Generate the static pages of Beautiful Danish Data from data/*.json.

Run `python3 build.py` after editing data/papers.json or data/variables.json.
"""
import hashlib
import html
import re
import json
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Changes whenever the stylesheet does, so a browser never pairs new pages with an old cached stylesheet
CSS_VERSION = hashlib.sha1((ROOT / "css" / "styles.css").read_bytes()).hexdigest()[:8]
PAPERS = json.loads((ROOT / "data" / "papers.json").read_text())
VARS = json.loads((ROOT / "data" / "variables.json").read_text())
_LPR = ROOT / "data" / "lpr.json"
LPR = json.loads(_LPR.read_text()) if _LPR.exists() else None
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
    <link rel="alternate" hreflang="en" href="{SITE}{canonical}">
    <link rel="alternate" hreflang="zh-Hans" href="{SITE}zh/{canonical}">
    <link rel="alternate" hreflang="x-default" href="{SITE}{canonical}">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="Beautiful Danish Data">
    <meta property="og:title" content="{e(title)}">
    <meta property="og:description" content="{e(description)}">
    <meta property="og:url" content="{SITE}{canonical}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="css/styles.css?v={CSS_VERSION}">
    <link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
</head>
<body>
"""


NAV_MAIN = [("index.html", "Summary"), ("papers.html", "Papers"), ("themes.html", "Themes"), ("samples.html", "Data & samples"), ("codebook.html", "Codebook")]
NAV_MORE = [("variables.html", "Variable map"), ("lifecycle.html", "Life course"), ("survey.html", "Survey"), ("network.html", "Author network"), ("schools.html", "Copenhagen vs Aarhus"), ("publication.html", "Publication analysis"), ("authors.html", "Authors and RAs")]


NAV_SCRIPT = """    <script>document.addEventListener('click', function (ev) { document.querySelectorAll('nav details[open]').forEach(function (d) { if (!d.contains(ev.target)) d.removeAttribute('open'); }); });</script>
"""


def nav(active):
    link = lambda href, label: f'<li><a href="{href}"' + (' class="active"' if href == active else "") + f'>{label}</a></li>'
    lis = "".join(link(h, l) for h, l in NAV_MAIN)
    in_more = any(h == active for h, _ in NAV_MORE)
    lis += ('<li class="more"><details><summary' + (' class="active"' if in_more else "") + '>More</summary><ul>'
            + "".join(link(h, l) for h, l in NAV_MORE) + "</ul></details></li>")
    return f"""    <header>
        <div class="container head-row">
            <div class="brand">
                <p class="eyebrow"><a href="{HOME}">Rentian Zhu</a> &rsaquo; Useful links</p>
                <h1><a href="index.html">Beautiful Danish Data</a> <span class="beta" title="Beta version: the list is still being checked and extended">Beta</span></h1>
                <p class="tagline">A field guide to economics published with Danish administrative data</p>
            </div>
            <div class="head-right">
                <p class="lang-switch"><span class="cur">EN</span><a href="zh/{active}" lang="zh-Hans" hreflang="zh-Hans">中文</a></p>
                <nav aria-label="Pages">
                    <ul>{lis}<li><a href="https://github.com/Zhurt0/beautiful-danish-data" target="_blank" rel="noopener">GitHub</a></li></ul>
                </nav>
            </div>
        </div>
    </header>
""" + NAV_SCRIPT


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


# ---------- selection note on the Summary page ----------
HOME_INTRO = "Denmark links every resident, firm, hospital visit, tax return and job to a single identifier, and lets researchers work with the whole population from the 1980s onwards. This page is a reading list of the economics that has come out of that infrastructure in the top general-interest journals and in the two leading field journals for labour and public economics: what question each paper asks, what it finds, and which registers it is built from."
SELECTION_AS_OF = "November 2026"
SELECTION_EXTRA = ("The list was then checked twice. The <em>Review of Economic Studies</em> for 2005&ndash;2018 was screened article by article "
                   "(titles and abstracts of all 710 articles in volumes 72&ndash;85), which added one paper, "
                   "Groes, Kircher and Manovskii (2015). In November 2026 every article listed for these journals on RePEc for "
                   "1998&ndash;2026 (about 23,500 articles) was screened by title, by author name and, where an abstract is online, by abstract. "
                   "This second check added 18 papers, two of which use Danish registers next to another country&rsquo;s data or an experiment. "
                   "About 4,000 articles have no abstract online and could only be screened by title and author: mostly the "
                   "<em>American Economic Review</em> before 2011, the <em>Journal of Public Economics</em> before 2010, the "
                   "<em>Economic Journal</em> for 2010&ndash;2017 and older volumes of the <em>Journal of Political Economy</em> and <em>Econometrica</em>.")
# Papers in which Denmark is one of several countries. They were left out until November 2026.
MULTI_COUNTRY = ["roemer2003", "bratsberg2007", "moscarini2012", "cosar2015", "eika2019", "bertheau2023", "butikofer2024", "kleven2025atlas"]


def selection_multi():
    by_id = {p["id"]: p for p in PAPERS}
    cites = ", ".join(f'<a href="papers.html#{i}">{e(short_cite(by_id[i]))}</a>' for i in MULTI_COUNTRY if i in by_id)
    n = sum(1 for i in MULTI_COUNTRY if i in by_id)
    return (f"Papers that use Danish register data as one of several countries were left out at first and have been included since "
            f"November 2026. {n} were added, each checked against the paper itself: {cites}. A paper counts when Danish register "
            f"microdata are among the country datasets it analyses.")


JOURNAL_ORDER = [
    "American Economic Review", "Quarterly Journal of Economics", "Journal of Political Economy", "Econometrica",
    "Review of Economic Studies", "AER: Insights", "AEJ: Applied Economics", "AEJ: Economic Policy",
    "AEJ: Macroeconomics", "Review of Economics and Statistics", "Economic Journal", "Journal of Labor Economics",
    "Journal of Public Economics",
]


def selection_journals():
    """The selected journals with the number of papers found in each."""
    counts = {}
    for p in PAPERS:
        j = p["journal"].replace(" (forthcoming)", "")
        counts[j] = counts.get(j, 0) + 1
    unknown = sorted(set(counts) - set(JOURNAL_ORDER))
    assert not unknown, f"journal not in JOURNAL_ORDER: {unknown}"
    return ", ".join(f"<em>{e(j)}</em> ({counts.get(j, 0)})" for j in JOURNAL_ORDER) + "."


def selection_by_period():
    """Papers per period, so the thinner early coverage is visible."""
    bins = [(None, 2004), (2005, 2009), (2010, 2014), (2015, 2019), (2020, 2024), (2025, None)]
    parts = []
    for lo, hi in bins:
        n = sum(1 for p in PAPERS if (lo is None or p["year"] >= lo) and (hi is None or p["year"] <= hi))
        if not n:
            continue
        label = f"up to {hi}" if lo is None else (f"{lo} onwards" if hi is None else f"{lo}&ndash;{hi}")
        parts.append(f"{label}: {n}")
    return "Papers by publication year: " + "; ".join(parts) + "."


def build_index():
    """The front page stays short: the opening, then the way into the papers. The full list is on papers.html."""
    counts = {g: sum(1 for p in PAPERS if p["group"] == g) for g, _, _ in GROUPS}
    out = head(
        "Beautiful Danish Data | Papers using Danish administrative data",
        "Summaries of Top 5, AEJ, Review of Economics and Statistics and Economic Journal papers that use Danish administrative register data, organised by journal, by theme and by variable.",
        "",
    )
    out += nav("index.html")
    out += home_hero()
    out += f"""    <section class="section intro">
        <div class="container">
            <h2 class="section-title">Papers by journal</h2>
            <p>{len(PAPERS)} papers from {len({p["journal"].replace(" (forthcoming)", "") for p in PAPERS})} journals, published {min(p["year"] for p in PAPERS)}&ndash;{max(p["year"] for p in PAPERS)}. Read them <a href="papers.html">by journal</a> or <a href="themes.html">by theme</a>, or see <a href="papers.html#selection">how the papers were selected</a>.</p>
            <ul class="counts">
{"".join(f'                <li><a href="papers.html#{g}">{e(n)}</a><span>{counts[g]}</span></li>' + chr(10) for g, n, _ in GROUPS)}            </ul>
        </div>
    </section>
    <script>/* old links pointed at papers on this page */ if (location.hash.length > 1 && !document.getElementById(location.hash.slice(1))) location.replace('papers.html' + location.hash);</script>
"""
    out += FOOTER
    return out


# Search on the Papers page: every word typed must appear somewhere in a paper's card (authors, title, journal,
# summary, data, variables, definitions). Accents are ignored, so "sorensen" finds "Sørensen".
PAPER_SEARCH = """    <script>
    (function () {
        var box = document.getElementById('pfilter'), count = document.getElementById('pcount');
        var cards = Array.prototype.slice.call(document.querySelectorAll('article.paper')), text = null;
        function plain(s) {
            return s.toLowerCase().replace(/ø/g, 'o').replace(/æ/g, 'ae').replace(/å/g, 'a').normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
        }
        function run() {
            var words = plain(box.value).split(/\s+/).filter(Boolean), n = 0;
            if (!text) text = cards.map(function (c) { return plain(c.textContent); });
            cards.forEach(function (c, i) {
                var hit = words.every(function (w) { return text[i].indexOf(w) >= 0; });
                c.hidden = !hit; if (hit) n++;
            });
            document.querySelectorAll('section.section[id]').forEach(function (s) {
                s.hidden = !s.querySelector('article.paper:not([hidden])');
            });
            document.body.classList.toggle('searching', words.length > 0);
            count.textContent = !words.length ? '' : n ? 'Showing {n} of {t} papers'.replace('{n}', n).replace('{t}', cards.length) : 'No papers match';
        }
        box.addEventListener('input', run);
        if (box.value) run();
    })();
    </script>
"""


def build_papers():
    counts = {g: sum(1 for p in PAPERS if p["group"] == g) for g, _, _ in GROUPS}
    out = head(
        "Papers | Beautiful Danish Data",
        "One-paragraph summaries of the papers built on Danish administrative register data, grouped by journal, with each paper's datasets, key variables, data period and sample size.",
        "papers.html",
    )
    out += nav("papers.html")
    out += f"""    <section class="section intro">
        <div class="container">
            <h2 class="section-title">By journal</h2>
            <input id="pfilter" class="filter" type="search" placeholder="Search papers: author, title, journal, register, variable or keyword" aria-label="Search papers" autocomplete="off">
            <p id="pcount" class="pcount muted" aria-live="polite"></p>
            <div class="selection" id="selection">
                <h3>How the papers were selected</h3>
                <dl>
                    <div><dt>Journals</dt><dd>{selection_journals()}</dd></div>
                    <div><dt>Period</dt><dd>Articles published from {min(p["year"] for p in PAPERS)} to {max(p["year"] for p in PAPERS)}, including articles accepted and forthcoming as of {SELECTION_AS_OF}. The earliest paper found is from {min(p["year"] for p in PAPERS)}. {selection_by_period()}</dd></div>
                    <div><dt>Search</dt><dd>A Crossref search of every article in these journals whose title or abstract mentions Denmark or Danish data, plus the publication lists of the main Danish research groups and authors, with each paper then checked by hand. {SELECTION_EXTRA}</dd></div>
                    <div><dt>Included</dt><dd>Papers that analyse Danish administrative register data, whether Denmark is the only country studied or one of several.</dd></div>
                    <div><dt>Several countries</dt><dd>{selection_multi()}</dd></div>
                    <div><dt>Excluded</dt><dd><em>AEA Papers and Proceedings</em>, finance journals, and papers whose only Danish input is aggregate statistics, a survey that is not linked to the registers, or a commercial database.</dd></div>
                </dl>
            </div>
            <p>The list covers {len(PAPERS)} papers. It will still miss papers whose title and abstract do not name the country, especially older ones whose abstracts are not in Crossref, so additions are welcome. Each paper lists its datasets, key variables, data period and sample size, and the <a href="samples.html">Data &amp; samples</a> page puts these in one sortable table. The <a href="themes.html">Themes</a> page regroups the same papers by topic, and the <a href="variables.html">Variable map</a> lists the registers and variables they rely on, at the individual and the firm level. If a paper is missing or a summary is wrong, open an issue or a pull request on GitHub.</p>
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
    out += PAPER_SEARCH
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
            f'<a href="papers.html#{pid}">{e(PAPER_BY_ID[pid]["authors"].split(",")[0].split(" and ")[0].split()[-1])} ({PAPER_BY_ID[pid]["year"]})</a>'
            for pid in r["used_by"] if pid in PAPER_BY_ID
        )
        used = f'                <p class="used-by"><strong>Used by:</strong> {links}</p>\n'
    more = lpr_details() if r["register"].startswith("LPR") and LPR else ""
    return f"""            <div class="register" id="reg-{slug(r['register'])}">
                <h3>{e(r['register'])}</h3>
                <p class="what">{e(r['what'])}</p>
                <table>
                    <thead><tr><th>Variable</th><th>Meaning</th></tr></thead>
                    <tbody>
{rows}                    </tbody>
                </table>
{used}{more}            </div>
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
        out += (f'                    <tr><td data-label="Paper"><a href="papers.html#{p["id"]}">{e(short_cite(p))}</a><br><span class="t">{e(p["title"])}</span></td>'
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
                    f'<td data-label="Paper"><a href="papers.html#{p["id"]}">{e(short_cite(p))}</a></td>'
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
            papers = ", ".join(f'<a href="papers.html#{pid}">{e(short_cite(by_id[pid]))}</a>' for pid in sv.get("papers", []) if pid in by_id)
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


LC_REG = {
    "BEF": "BEF — Population register", "VNDS": "VNDS / Residence histories", "MFR": "MFR — Medical Birth Register",
    "LPR": "LPR — National Patient Register", "LMDB": "LMDB — Prescription register", "DOD": "DOD — Death register",
    "UDDA": "UDDA — Education register", "IDA": "IDA / IDAN / IDAP — Integrated labour market database",
    "AKM": "AKM — Labour market classification", "BFL": "BFL / eIndkomst — Monthly payroll",
    "IND": "IND — Income register", "FORM": "FORM — Wealth register", "DREAM": "DREAM — Public transfers (weekly)",
    "KRAF": "KRAF / KRSI — Crime registers",
}
# lanes of the chart: group, then (key, ages at which the register follows a person)
LC_LANES = [
    ("Who you are and where you live", [("BEF", [(0, 95)]), ("VNDS", [(0, 95)])]),
    ("Health", [("MFR", [(0, 0.6), (20, 45)]), ("LPR", [(0, 95)]), ("LMDB", [(0, 95)]), ("DOD", [])]),
    ("Education", [("UDDA", [(5, 30)])]),
    ("Work", [("IDA", [(15, 74)]), ("AKM", [(15, 95)]), ("BFL", [(15, 70)]), ("FIRMS", [(16, 67)])]),
    ("Money", [("IND", [(15, 95)]), ("FORM", [(18, 95)]), ("DREAM", [(16, 95)])]),
    ("Crime", [("KRAF", [(15, 95)])]),
]
LC_EVENTS = [
    ("Birth", 0, 0, 0, "A person enters the registers the day they are born in Denmark.",
     [("MFR", "Birth weight, gestational age and Apgar score, linked to the mother"),
      ("BEF", "A personal number (PNR) is created, with mother's and father's PNR and municipality"),
      ("LPR", "The birth stay and any neonatal admissions"),
      ("VNDS", "First address")]),
    ("Childhood health care", 5, 0, 15, "Hospital visits and medicines from the first years of life.",
     [("LPR", "Every hospital contact with diagnoses (ICD-10) and dates"),
      ("LMDB", "Every prescription filled at a pharmacy (ATC code, date, amount)")]),
    ("Starting school", 6, 5, 7, "School enrolment starts the education record.",
     [("UDDA", "Enrolment spells by programme (KOTRE) from the first school year")]),
    ("Parents separate or the family moves", 9, 0, 17, "Changes in the household while growing up.",
     [("BEF", "Family ID and family type change; parents' marital status"),
      ("VNDS", "Each move, with date, municipality and parish")]),
    ("End of compulsory school", 16, 15, 17, "Lower secondary school is completed.",
     [("UDDA", "Primary and lower secondary becomes the highest completed education (HFAUDD)")]),
    ("Contact with the police", 19, 15, 30, "Danish criminal responsibility starts at 15; charges peak in the late teens and twenties.",
     [("KRAF", "Charges and convictions with offence code, decision type and dates")]),
    ("First job", 18, 15, 25, "Student jobs and the first regular job link the person to an employer.",
     [("IDA", "Employer (CVRNR), workplace, occupation (DISCO) and hourly wage for the November job"),
      ("BFL", "Monthly pay, paid hours and job start date (from 2008)"),
      ("AKM", "Socio-economic status changes to employed"),
      ("IND", "Wage income for the year"),
      ("FIRMS", "The employer's industry, size, accounts and trade, through the firm-worker link")]),
    ("Upper secondary or vocational school", 18, 16, 20, "Gymnasium or a vocational programme.",
     [("UDDA", "Programme spells, start and completion dates")]),
    ("Leaving home", 20, 18, 24, "Moving out of the parents' household.",
     [("BEF", "A new family ID, no longer counted in the parents' family"),
      ("VNDS", "New address and move date")]),
    ("Higher education", 22, 19, 28, "University or professional degree.",
     [("UDDA", "Programme, start and completion dates, new highest education"),
      ("DREAM", "Weeks on the state study grant (SU)")]),
    ("Arriving in Denmark", 27, 0, 60, "For immigrants, the record starts on arrival rather than at birth.",
     [("BEF", "Origin type (immigrant, descendant) and country of origin"),
      ("VNDS", "Immigration date and first address"),
      ("UDDA", "Foreign qualifications are only partly covered; Statistics Denmark filled gaps with a survey (see the Survey page)")]),
    ("Moving in together or marrying", 29, 24, 35, "Forming a couple.",
     [("BEF", "Partner's PNR, marital status and a shared family ID"),
      ("VNDS", "Shared address")]),
    ("Having children", 31, 25, 40, "The person now appears as a parent, and the child's records link back to them.",
     [("MFR", "Recorded as the mother or father; the child's birth outcomes"),
      ("BEF", "The child is linked through MOR_PNR / FAR_PNR"),
      ("LPR", "Pregnancy and birth admissions for the mother"),
      ("DREAM", "Weeks of parental leave benefit"),
      ("BFL", "Monthly hours and pay around the birth")]),
    ("Buying a home", 32, 25, 40, "Becoming a home owner.",
     [("FORM", "Property value, mortgage and bank debt at year end"),
      ("IND", "Interest expenses"),
      ("VNDS", "Move date and new address")]),
    ("Changing job or being promoted", 38, 20, 60, "Moving between employers or up the hierarchy.",
     [("IDA", "New employer and workplace, occupation (DISCO), tenure"),
      ("BFL", "Exact start and end dates of each job"),
      ("FIRMS", "The new employer's characteristics"),
      ("IND", "Change in earnings")]),
    ("Separation or divorce", 42, 30, 55, "A couple splits up.",
     [("BEF", "Marital status and family ID change; the partner link ends"),
      ("VNDS", "One partner moves out"),
      ("FORM", "Assets and debts now recorded separately")]),
    ("Job loss and unemployment", 45, 20, 64, "Losing a job and searching for a new one.",
     [("BFL", "Job end date; monthly pay stops"),
      ("DREAM", "Weeks on unemployment insurance or social assistance"),
      ("IDA", "Degree of unemployment over the year"),
      ("AKM", "Status changes to unemployed"),
      ("IND", "Public transfers received")]),
    ("Illness and sick leave", 50, 20, 65, "A health shock during working life.",
     [("LPR", "Diagnoses and admission dates"),
      ("LMDB", "Prescriptions filled"),
      ("DREAM", "Weeks on sickness benefit"),
      ("BFL", "Hours and pay during and after the illness")]),
    ("Disability pension or early retirement", 60, 50, 64, "Leaving the labour market before pension age.",
     [("DREAM", "Weeks on disability pension or voluntary early retirement"),
      ("AKM", "Status changes to outside the labour force"),
      ("IND", "Transfer income")]),
    ("Retirement", 67, 62, 70, "Reaching pension age.",
     [("DREAM", "Public old-age pension"),
      ("IND", "Pension income"),
      ("FORM", "Pension wealth (later years)"),
      ("AKM", "Status changes to retired"),
      ("BFL", "The last month of pay")]),
    ("Health care in old age", 78, 70, 90, "Hospital use and medicines rise steeply.",
     [("LPR", "Hospital contacts and diagnoses"),
      ("LMDB", "Prescriptions filled")]),
    ("Death", 82, 60, 95, "The record ends.",
     [("DOD", "Date of death and underlying and contributing causes (ICD-10)"),
      ("BEF", "The person leaves the population"),
      ("LPR", "The last hospital contacts")]),
]


def build_lifecycle():
    regs = {r["register"]: r for r in VARS["individual"] + VARS["firm"]}
    firm_used = sorted({pid for r in VARS["firm"] for pid in r["used_by"]})
    lanes, info = [], {}
    for k, full in LC_REG.items():
        info[k] = dict(name=REG_SHORT[full], full=full, n=len(regs[full]["used_by"]), href="variables.html#reg-" + slug(full))
    info["FIRMS"] = dict(name="Employer's firm registers", full="FIDA, FIRM/FIRE, foreign trade, VAT and company registers",
                         n=len(firm_used), href="variables.html#firm")
    for g, ls in LC_LANES:
        lanes.append(dict(group=g, regs=[dict(k=k, spans=sp) for k, sp in ls]))
    events = sorted(LC_EVENTS, key=lambda x: (x[1], x[2]))
    ev = [dict(name=n, age=a, lo=lo, hi=hi, desc=d, regs=[dict(k=k, what=w) for k, w in rs]) for n, a, lo, hi, d, rs in events]
    n_reg = len(info)

    out = head(
        "Life course | Beautiful Danish Data",
        "The main events in a person's life, from birth to death, and the Danish registers that record each one.",
        "lifecycle.html",
    )
    out += nav("lifecycle.html")
    out += f"""    <section class="section intro">
        <div class="container">
            <h2 class="section-title">Life course in the registers</h2>
            <p>A person living in Denmark leaves a trace in the registers at almost every turn of life. The chart follows one life from birth to death: the numbered events along the top are the main things that happen to people, and each row below is a register. A light blue bar shows the ages over which a register follows a person, and a dot marks an event that the register records.</p>
            <p class="note">Ages are typical ages, for illustration. What exists also depends on the calendar year: monthly payroll (BFL) starts in 2008, prescriptions (LMDB) in 1995, weekly transfers (DREAM) in 1991, hospital records (LPR) in 1977 with outpatients from 1995, and the crime registers in 1980. Paper counts refer to the {len(PAPERS)} papers on this site. Income (IND), wealth (FORM) and labour-market status (AKM) are also updated every year whether or not anything happens.</p>
        </div>
    </section>
    <section class="section viz-section">
        <div class="container">
            <div class="lc-legend"><span><svg width="34" height="10" aria-hidden="true"><rect x="1" y="2" width="32" height="6" rx="3" fill="#a2deed"/></svg> The register follows the person over these ages</span><span><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="4.5" fill="#03045e" stroke="#ffffff" stroke-width="2"/></svg> The register records this event</span><span><svg width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="6" fill="#3375b1" stroke="#ffffff" stroke-width="2"/></svg> Selected</span></div>
            <div class="lc-scroll"><div id="lc" class="lc-chart" role="img" aria-label="Life-course chart: {len(ev)} life events by age, and the {n_reg} registers that record them. The table below gives the same information."></div></div>
            <p class="viz-help">Hover or click an event number to see which registers record it and the range of ages it usually happens at; hover or click a register to see its events. On a phone, scroll the chart sideways.</p>
            <div id="lc-panel" class="lc-panel" aria-live="polite"></div>

            <h3 class="sub-title">Events and the registers that record them</h3>
            <div class="table-wrap"><table class="lc-table">
                <thead><tr><th>#</th><th>Event</th><th>Typical ages</th><th>Registers and what they record</th></tr></thead>
                <tbody>
"""
    for i, x in enumerate(ev, 1):
        ages = f'{x["lo"]}&ndash;{x["hi"]}' if x["hi"] > x["lo"] else str(x["lo"])
        items = "".join(f'<li><a href="{info[r["k"]]["href"]}">{e(info[r["k"]]["name"])}</a>: {e(r["what"])}</li>' for r in x["regs"])
        out += (f'                    <tr id="ev-{i}"><td data-label="#">{i}</td><td data-label="Event"><strong>{e(x["name"])}</strong><br><span class="t">{e(x["desc"])}</span></td>'
                f'<td data-label="Typical ages">{ages}</td><td data-label="Registers"><ul>{items}</ul></td></tr>\n')
    out += """                </tbody>
            </table></div>
        </div>
    </section>
"""
    payload = json.dumps(dict(lanes=lanes, info=info, events=ev), ensure_ascii=False).replace("</", "<\\/")
    out += LIFECYCLE_JS.replace("__DATA__", payload)
    out += FOOTER
    return out


LIFECYCLE_JS = r"""    <script>
    (function () {
        var D = __DATA__;
        var NS = 'http://www.w3.org/2000/svg';
        var ACC = '#3375b1', INK = '#03045e', INK2 = '#4a5672', MUTED = '#76839b', GRID = '#dcebf2', BAR = '#a2deed', SURF = '#ffffff';
        var W = 1000, LW = 250, X0 = LW + 12, X1 = W - 20, AMAX = 95;
        function x(a) { return X0 + (X1 - X0) * a / AMAX; }
        function el(tag, attrs, parent) {
            var n = document.createElementNS(NS, tag);
            for (var k in attrs) n.setAttribute(k, attrs[k]);
            if (parent) parent.appendChild(n);
            return n;
        }
        function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

        // stack event markers into rows so that numbered circles never overlap
        var rowsEnd = [], ER = 11;
        D.events.forEach(function (ev, i) {
            ev.i = i; ev.num = i + 1;
            var px = x(ev.age), r = 0;
            while (rowsEnd[r] !== undefined && rowsEnd[r] > px - 2 * ER - 4) r++;
            rowsEnd[r] = px; ev.row = r;
        });
        var nRows = rowsEnd.length, TOP = 18, RH = 28, evH = TOP + nRows * RH;
        var AXIS = evH + 20;
        var y = AXIS + 14, laneY = {}, layout = [];
        D.lanes.forEach(function (g) {
            layout.push({ type: 'group', label: g.group, y: y + 12 }); y += 22;
            g.regs.forEach(function (r) { laneY[r.k] = y + 13; layout.push({ type: 'lane', k: r.k, spans: r.spans, y: y + 13 }); y += 27; });
            y += 4;
        });
        var H = y + 6;
        var box = document.getElementById('lc');
        var svg = el('svg', { viewBox: '0 0 ' + W + ' ' + H, width: '100%', 'font-family': 'system-ui, -apple-system, "Segoe UI", sans-serif' }, box);

        // highlight band (behind everything)
        var band = el('rect', { x: 0, y: evH - 4, width: 0, height: H - evH, fill: ACC, 'fill-opacity': 0.07, visibility: 'hidden' }, svg);
        var bandLine = el('line', { y1: evH - 4, y2: H, stroke: ACC, 'stroke-width': 1, 'stroke-dasharray': '3 3', visibility: 'hidden' }, svg);

        // age axis and grid
        for (var a = 0; a <= 90; a += 10) {
            el('line', { x1: x(a), x2: x(a), y1: AXIS + 4, y2: H, stroke: GRID, 'stroke-width': 1 }, svg);
            var t = el('text', { x: x(a), y: AXIS, 'text-anchor': 'middle', 'font-size': 12, fill: INK2 }, svg); t.textContent = a;
        }
        var at = el('text', { x: LW, y: AXIS, 'text-anchor': 'end', 'font-size': 12, fill: INK2 }, svg); at.textContent = 'Age';

        // lanes
        var laneEls = {};
        layout.forEach(function (L) {
            if (L.type === 'group') {
                var gt = el('text', { x: 0, y: L.y, 'font-size': 11, 'font-weight': 700, fill: INK2, 'letter-spacing': '0.04em' }, svg);
                gt.textContent = L.label.toUpperCase();
                return;
            }
            var info = D.info[L.k];
            var g = el('g', { 'class': 'lc-lane', 'data-k': L.k, tabindex: 0, role: 'button', 'aria-label': info.name }, svg);
            el('rect', { x: 0, y: L.y - 13, width: W, height: 26, fill: 'transparent' }, g);
            var lt = el('text', { x: 8, y: L.y + 4, 'font-size': 13, fill: INK }, g); lt.textContent = info.name;
            var nt = el('text', { x: LW, y: L.y + 4, 'font-size': 11, 'text-anchor': 'end', fill: MUTED }, g); nt.textContent = info.n + (info.n === 1 ? ' paper' : ' papers');
            L.spans.forEach(function (s) {
                el('rect', { x: x(s[0]), y: L.y - 3, width: Math.max(x(s[1]) - x(s[0]), 6), height: 6, rx: 3, fill: BAR }, g);
            });
            laneEls[L.k] = g;
        });

        // dots: one per (event, register)
        var dots = [];
        D.events.forEach(function (ev) {
            ev.regs.forEach(function (r) {
                var c = el('circle', { cx: x(ev.age), cy: laneY[r.k], r: 4.5, fill: INK2, stroke: SURF, 'stroke-width': 2, 'class': 'lc-dot' }, svg);
                c.__d = { ev: ev, r: r }; dots.push(c);
            });
        });

        // event markers
        var evEls = [];
        D.events.forEach(function (ev) {
            var cy = TOP + ev.row * RH + 4;
            var g = el('g', { 'class': 'lc-ev', tabindex: 0, role: 'button', 'aria-label': ev.num + '. ' + ev.name }, svg);
            el('circle', { cx: x(ev.age), cy: cy, r: ER + 6, fill: 'transparent' }, g);
            var c = el('circle', { cx: x(ev.age), cy: cy, r: ER, fill: SURF, stroke: INK2, 'stroke-width': 1.5 }, g);
            var tx = el('text', { x: x(ev.age), y: cy + 4, 'text-anchor': 'middle', 'font-size': 11, 'font-weight': 700, fill: INK }, g);
            tx.textContent = ev.num;
            g.__ev = ev; g.__c = c; g.__t = tx; evEls.push(g);
        });

        var tip = document.createElement('div'); tip.className = 'net-tip'; tip.style.display = 'none'; box.appendChild(tip);
        var panel = document.getElementById('lc-panel'), sticky = null;

        function paint(sel) {
            var evSel = sel && sel.type === 'ev' ? sel.ev : null, kSel = sel && sel.type === 'reg' ? sel.k : null;
            var involved = {};
            if (evSel) evSel.regs.forEach(function (r) { involved[r.k] = 1; });
            dots.forEach(function (c) {
                var on = (evSel && c.__d.ev === evSel) || (kSel && c.__d.r.k === kSel);
                c.setAttribute('fill', on ? ACC : INK2); c.setAttribute('r', on ? 6 : 4.5);
                c.setAttribute('opacity', sel && !on ? 0.25 : 1);
            });
            evEls.forEach(function (g) {
                var on = (evSel && g.__ev === evSel) || (kSel && g.__ev.regs.some(function (r) { return r.k === kSel; }));
                g.__c.setAttribute('fill', on ? ACC : SURF); g.__c.setAttribute('stroke', on ? ACC : INK2);
                g.__t.setAttribute('fill', on ? '#ffffff' : INK); g.setAttribute('opacity', sel && !on ? 0.35 : 1);
            });
            Object.keys(laneEls).forEach(function (k) {
                var on = (evSel && involved[k]) || kSel === k;
                laneEls[k].setAttribute('opacity', sel && !on ? 0.35 : 1);
                laneEls[k].querySelector('text').setAttribute('font-weight', on ? 700 : 400);
            });
            if (evSel) {
                band.setAttribute('x', x(evSel.lo) - 6); band.setAttribute('width', x(evSel.hi) - x(evSel.lo) + 12); band.setAttribute('visibility', 'visible');
                bandLine.setAttribute('x1', x(evSel.age)); bandLine.setAttribute('x2', x(evSel.age)); bandLine.setAttribute('visibility', 'visible');
            } else { band.setAttribute('visibility', 'hidden'); bandLine.setAttribute('visibility', 'hidden'); }
        }
        function ages(ev) { return ev.hi > ev.lo ? ev.lo + '–' + ev.hi : String(ev.lo); }
        function describe(sel) {
            if (!sel) {
                panel.innerHTML = '<p class="muted">Select an event number or a register in the chart. ' + D.events.length + ' events, ' + Object.keys(D.info).length + ' registers.</p>';
                return;
            }
            var h;
            if (sel.type === 'ev') {
                var ev = sel.ev;
                h = '<h3>' + ev.num + '. ' + esc(ev.name) + ' <span class="muted">(typical ages ' + ages(ev) + ')</span></h3><p>' + esc(ev.desc) + '</p><ul>';
                ev.regs.forEach(function (r) { var i = D.info[r.k]; h += '<li><a href="' + i.href + '"><strong>' + esc(i.name) + '</strong></a> <span class="muted">(' + i.n + ' papers)</span>: ' + esc(r.what) + '</li>'; });
                h += '</ul>';
            } else {
                var i = D.info[sel.k], evs = D.events.filter(function (ev) { return ev.regs.some(function (r) { return r.k === sel.k; }); });
                h = '<h3><a href="' + i.href + '">' + esc(i.name) + '</a> <span class="muted">' + esc(i.full) + ', used by ' + i.n + ' papers</span></h3>';
                h += evs.length ? '<ul>' : '<p class="muted">Follows the person every year; no single event.</p>';
                evs.forEach(function (ev) { var r = ev.regs.filter(function (r) { return r.k === sel.k; })[0]; h += '<li><strong>' + ev.num + '. ' + esc(ev.name) + '</strong> <span class="muted">(' + ages(ev) + ')</span>: ' + esc(r.what) + '</li>'; });
                if (evs.length) h += '</ul>';
            }
            panel.innerHTML = h;
        }
        function show(sel, isSticky) { if (isSticky) sticky = sel; paint(sel); describe(sel); }
        function release() { paint(sticky); describe(sticky); }
        function place(ev, html) {
            var r = box.getBoundingClientRect();
            tip.innerHTML = html; tip.style.display = 'block';
            var left = ev.clientX - r.left + 14; if (left > r.width - 250) left = ev.clientX - r.left - 250;
            tip.style.left = left + 'px'; tip.style.top = (ev.clientY - r.top + 14) + 'px';
        }
        evEls.forEach(function (g) {
            var sel = { type: 'ev', ev: g.__ev };
            g.addEventListener('mouseenter', function () { paint(sel); describe(sel); });
            g.addEventListener('mousemove', function (e) { place(e, '<strong>' + g.__ev.num + '. ' + esc(g.__ev.name) + '</strong><br>Typical ages ' + ages(g.__ev) + '<br>' + g.__ev.regs.length + ' registers'); });
            g.addEventListener('mouseleave', function () { tip.style.display = 'none'; release(); });
            g.addEventListener('click', function (e) { e.stopPropagation(); show(sel, true); });
            g.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); show(sel, true); } });
        });
        Object.keys(laneEls).forEach(function (k) {
            var g = laneEls[k], sel = { type: 'reg', k: k };
            g.addEventListener('mouseenter', function () { paint(sel); describe(sel); });
            g.addEventListener('mouseleave', release);
            g.addEventListener('click', function (e) { e.stopPropagation(); show(sel, true); });
            g.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); show(sel, true); } });
        });
        dots.forEach(function (c) {
            c.addEventListener('mousemove', function (e) { var d = c.__d; place(e, '<strong>' + esc(D.info[d.r.k].name) + '</strong><br>' + d.ev.num + '. ' + esc(d.ev.name) + '<br>' + esc(d.r.what)); });
            c.addEventListener('mouseleave', function () { tip.style.display = 'none'; });
            c.addEventListener('click', function (e) { e.stopPropagation(); show({ type: 'ev', ev: c.__d.ev }, true); });
        });
        svg.addEventListener('click', function () { show(null, true); });
        describe(null);
    })();
    </script>
"""


_NW = ROOT / "data" / "network.json"
NETWORK = json.loads(_NW.read_text()) if _NW.exists() else None
# One palette for the whole site ("Ocean Breeze"); groups differ by lightness, not hue
NAVY, BLUE, SKY, PALE, MIST = "#03045e", "#3375b1", "#50b1d4", "#a2deed", "#d1eff7"
NET_GROUPS = [("Danish universities", NAVY), ("Other Danish institutions", BLUE),
              ("Institutions abroad", SKY), ("Not listed", "#c3cbd6")]

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
        var link = g.append('g').attr('stroke', '#c9dbe5').attr('stroke-linecap', 'round').selectAll('line').data(links).join('line')
            .attr('x1', function (l) { return l.source.x; }).attr('y1', function (l) { return l.source.y; })
            .attr('x2', function (l) { return l.target.x; }).attr('y2', function (l) { return l.target.y; })
            .attr('stroke-width', function (l) { return 0.8 + 1.1 * (l.w - 1); }).attr('stroke-opacity', 0.75);
        var node = g.append('g').selectAll('circle').data(nodes).join('circle')
            .attr('cx', function (n) { return n.x; }).attr('cy', function (n) { return n.y; }).attr('r', r)
            .attr('fill', function (n) { return COLOR[n.group]; }).attr('stroke', '#ffffff').attr('stroke-width', 1)
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
            }).attr('stroke', function (n) { return n.i === focus ? '#03045e' : '#ffffff'; }).attr('stroke-width', function (n) { return n.i === focus ? 2 : 1; });
            link.attr('stroke-opacity', function (l) {
                if (near) return (l.source.i === focus || l.target.i === focus) ? 0.95 : 0.06;
                if (inst) return (l.source.institutions.indexOf(inst) >= 0 && l.target.institutions.indexOf(inst) >= 0) ? 0.9 : 0.06;
                return 0.75;
            }).attr('stroke', function (l) { return near && (l.source.i === focus || l.target.i === focus) ? '#03045e' : '#c9dbe5'; });
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
            n.papers.forEach(function (pid) { var p = D.papers[pid]; h += '<li><a href="papers.html#' + pid + '">' + esc(p.cite) + '</a>, <em>' + esc(p.title) + '</em></li>'; });
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
    legend = "".join(f'<span class="lg"><span class="sw" style="background:{c}"></span>{e(g)} <span class="muted">({cnt[g]})</span></span>' for g, c in NET_GROUPS if cnt[g])
    opts = "".join(f'<option value="{e(k)}">{e(k)} ({len(inst[k])})</option>' for k in inst_rows if len(inst[k]) >= 2)
    names = "".join(f'<option value="{e(n["name"])}"></option>' for n in sorted(nodes, key=lambda n: n["name"]))
    out += f"""    <section class="section intro">
        <div class="container">
            <h2 class="section-title">Author network</h2>
            <p class="scope-note"><strong>This network only covers papers that use Danish data.</strong> It is built from the {len(PAPERS)} papers on this site, so an author&rsquo;s papers, co-authors and position here reflect only that work, not their research as a whole.</p>
            <p>Every author of the {len(PAPERS)} papers, linked to everyone they wrote one of these papers with. {len(nodes)} authors and {len(nw["links"])} co-author pairs. {biggest} authors are joined in one connected group; {solo} wrote all their papers here alone.</p>
            <p class="note">Names are spelled as on the papers. Affiliations are those listed for each paper, taken mostly from OpenAlex; where that source was wrong or empty they were checked against the published byline, and for papers added later they come from the paper or its publisher record. Colour shows where an author was based on most of their papers here. Research networks such as NBER, CEPR, IZA and CESifo are left out, since nearly everyone lists one. If your name or affiliation is wrong, or a paper of yours is missing, please open an issue on GitHub.</p>
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
        ps = "; ".join(f'<a href="papers.html#{pid}">{e(nw["papers"][pid]["cite"])}</a>' for pid in l["papers"])
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


# ---------- Copenhagen vs Aarhus ----------
SCHOOLS = ("University of Copenhagen", "Aarhus University")


def fisher_p(a, b, c, d):
    """Two-sided Fisher exact test for the table [[a, b], [c, d]]."""
    from math import comb
    n, r1, c1 = a + b + c + d, a + b, a + c
    prob = lambda x: comb(r1, x) * comb(n - r1, c1 - x) / comb(n, c1)
    p0 = prob(a)
    return min(1.0, sum(prob(x) for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1) if prob(x) <= p0 * (1 + 1e-9)))


def schools_data():
    ku_name, au_name = SCHOOLS
    where = {}
    for n in NETWORK["nodes"]:
        if n["primary"]:
            for pid in n["papers"]:
                where.setdefault(pid, set()).add(n["primary"][0])
    ku = [p for p in PAPERS if ku_name in where.get(p["id"], ()) and au_name not in where.get(p["id"], ())]
    au = [p for p in PAPERS if au_name in where.get(p["id"], ()) and ku_name not in where.get(p["id"], ())]
    both = [p for p in PAPERS if ku_name in where.get(p["id"], ()) and au_name in where.get(p["id"], ())]
    rows = []
    for k, name, _ in THEMES:
        x, y = sum(k in p["themes"] for p in ku), sum(k in p["themes"] for p in au)
        if x + y < 5:
            continue
        rows.append((100 * x / len(ku) - 100 * y / len(au), name, x, y, fisher_p(x, len(ku) - x, y, len(au) - y)))
    rows.sort(key=lambda r: -r[0])
    return ku, au, both, rows


def build_schools():
    ku, au, both, rows = schools_data()
    bonf = 0.05 / len(rows)
    sig = [r for r in rows if r[4] < 0.05]
    strict = [r for r in rows if r[4] < bonf]
    t5k, t5a = sum(p["group"] == "top5" for p in ku), sum(p["group"] == "top5" for p in au)
    p_top5 = fisher_p(t5k, len(ku) - t5k, t5a, len(au) - t5a)

    def cell(x, n, cls):
        share = 100 * x / n
        return (f'<td class="sch" data-label="{cls}"><span class="sbar"><i class="{cls}" style="width:{share:.0f}%"></i></span>'
                f'<span class="sval">{share:.0f}%</span> <span class="muted">{x}/{n}</span></td>')

    def pfmt(p):
        return "&lt;0.001" if p < 0.001 else f"{p:.3f}"

    def names(rs):
        ns = [r[1].split(",")[0].split(" and ")[0].lower() for r in rs]
        return ns[0] if len(ns) == 1 else ", ".join(ns[:-1]) + " and " + ns[-1]

    more_ku = [r for r in sig if r[0] > 0]; more_au = [r for r in sig if r[0] < 0]
    out = head(
        "Copenhagen vs Aarhus | Beautiful Danish Data",
        "The University of Copenhagen and Aarhus University both publish with Danish register data, but on different topics: a comparison of themes across the two groups of papers.",
        "schools.html",
    )
    out += nav("schools.html")
    out += f"""    <section class="section intro">
        <div class="container">
            <h2 class="section-title">Copenhagen and Aarhus do two kinds of economics</h2>
            <p>Of the {len(PAPERS)} papers on this site, {len(ku)} have an author based at the University of Copenhagen and none at Aarhus University, and {len(au)} have an author at Aarhus and none at Copenhagen. Only {len(both)} have authors from both. The two groups work with the same registers but ask different questions: Copenhagen papers are more often about {names(more_ku) if more_ku else "the same themes"}, Aarhus papers about {names(more_au) if more_au else "the same themes"}.</p>
            <div class="table-wrap">
                <table class="schools">
                    <thead><tr><th>Theme</th><th>Copenhagen <span class="muted">({len(ku)} papers)</span></th><th>Aarhus <span class="muted">({len(au)} papers)</span></th><th>Difference</th><th><em>p</em>-value</th></tr></thead>
                    <tbody>
"""
    for diff, name, x, y, pv in rows:
        mark = ' class="sig"' if pv < 0.05 else ""
        out += (f'                        <tr{mark}><td data-label="Theme">{e(name)}</td>{cell(x, len(ku), "ku")}{cell(y, len(au), "au")}'
                f'<td data-label="Difference">{("0" if round(diff) == 0 else f"{diff:+.0f}")} pp</td><td data-label="p-value">{pfmt(pv)}{"*" if pv < bonf else ""}</td></tr>\n')
    out += f"""                    </tbody>
                </table>
            </div>
            <p class="note">Share of each group's papers that carry the theme; a paper can carry several themes, so columns do not sum to 100. Themes with fewer than five papers across the two groups are left out. <em>p</em>-values are from two-sided Fisher exact tests; rows in bold are below 0.05. With {len(rows)} themes tested, a Bonferroni-corrected threshold is {bonf:.4f}: {("only " + names(strict) + (" passes" if len(strict) == 1 else " pass") + " it (marked *)") if strict else "no theme passes it"}, so read the other differences as suggestive.</p>
        </div>
    </section>
    <section class="section">
        <div class="container">
            <h2 class="section-title">Same journals, different topics</h2>
            <p>The two groups reach the Top 5 journals at similar rates: {t5k} of {len(ku)} Copenhagen papers ({100 * t5k / len(ku):.0f}%) and {t5a} of {len(au)} Aarhus papers ({100 * t5a / len(au):.0f}%), a difference that is not statistically significant (Fisher exact <em>p</em> = {p_top5:.2f}).</p>
            <p class="note">How papers are assigned: an author's affiliation is the first institution listed for them on the <a href="network.html">Author network</a> page. A paper counts for a university if at least one of its authors is based there, so co-authors from other institutions do not change the assignment. The comparison covers only papers published in the journals on this list, and affiliations taken from publication records can be out of date.</p>
"""
    for label, ps in ((f"The {len(ku)} Copenhagen papers", ku), (f"The {len(au)} Aarhus papers", au), (f"The {len(both)} papers with authors from both", both)):
        items = "".join(f'<li><a href="papers.html#{p["id"]}">{e(short_cite(p))}</a>, <em>{e(p["title"])}</em></li>' for p in sorted(ps, key=lambda p: (-p["year"], p["authors"])))
        out += f'            <details class="net-all"><summary>{e(label)}</summary><ul class="plain">{items}</ul></details>\n'
    out += """        </div>
    </section>
"""
    out += FOOTER
    return out


# ---------- National Patient Register (LPR) ----------
def lpr_refs(keys):
    return ' <span class="refs">' + "; ".join(f'<a href="#src-{k}">{e(LPR["sources"][k]["short"])}</a>' for k in keys) + "</span>"


def lpr_details():
    """Everything about the National Patient Register, shown inside its block on the Variable map."""
    L = LPR
    reg = next(r for r in VARS["individual"] if r["register"].startswith("LPR"))
    touches = lambda d: any(re.search(r"\bLPR\b|patient regist", x, re.I) for x in d.get("registers", [])) or bool(re.search(r"\bLPR\b", d.get("definition", "")))
    use = {}
    for p in PAPERS:
        ds = [d for d in p.get("definitions", []) if touches(d)]
        if p["id"] in reg["used_by"] or ds:
            use[p["id"]] = ds
    papers = sorted((PAPER_BY_ID[i] for i in use), key=lambda p: (p["year"], p["authors"]))
    n_defs = sum(len(v) for v in use.values())
    bins = [("up to 2019", lambda y: y <= 2019), ("2020&ndash;2024", lambda y: 2020 <= y <= 2024), ("2025 onwards", lambda y: y >= 2025)]
    by_period = "; ".join(f"{lab}: {sum(1 for p in papers if f(p['year']))}" for lab, f in bins)
    first = papers[0]
    codes = lambda t: "<br>".join(f"<code>{e(x)}</code>" for x in t.split(", "))

    out = f"""                <details class="reg-more" id="lpr">
                    <summary>More on this register: history, content, variables and pitfalls</summary>
                    <p>{e(L["summary"])}{lpr_refs(L["summary_src"])}</p>
                    <div class="selection">
                        <h3>At a glance</h3>
                        <dl>
"""
    for lab, val, src in L["key_facts"]:
        out += f'                            <div><dt>{e(lab)}</dt><dd>{e(val)}{lpr_refs(src)}</dd></div>\n'
    out += """                        </dl>
                    </div>
                    <h4>How it grew</h4>
                    <p class="blurb">The register did not start as the all-contacts register it is today. Each extension is also a break in any series that runs across it.</p>
                    <div class="table-wrap"><table class="lpr">
                        <thead><tr><th>Year</th><th>What changed</th></tr></thead>
                        <tbody>
"""
    for year, ev, src in L["timeline"]:
        out += f'                            <tr><td data-label="Year"><strong>{e(year)}</strong></td><td data-label="What changed">{e(ev)}{lpr_refs(src)}</td></tr>\n'
    out += f"""                        </tbody>
                    </table></div>
                    <p class="note">{e(L["timeline_note"])}</p>
                    <h4>What a record contains</h4>
                    <div class="table-wrap"><table class="lpr">
                        <thead><tr><th>Part</th><th>What is recorded</th></tr></thead>
                        <tbody>
"""
    for item, detail, src in L["content"]:
        out += f'                            <tr><td data-label="Part"><strong>{e(item)}</strong></td><td data-label="What is recorded">{e(detail)}{lpr_refs(src)}</td></tr>\n'
    out += f"""                        </tbody>
                    </table></div>
                    <h4>Tables and variables</h4>
                    <p>{e(L["tables_note"])}{lpr_refs(L["tables_src"])}</p>
                    <div class="table-wrap"><table class="lpr">
                        <thead><tr><th>Variable</th><th>Meaning</th><th>Table</th></tr></thead>
                        <tbody>
"""
    for name, meaning, table, src in L["variables"]:
        out += (f'                            <tr><td data-label="Variable">{codes(name)}</td><td data-label="Meaning">{e(meaning)}{lpr_refs(src)}</td>'
                f'<td data-label="Table">{codes(table)}</td></tr>\n')
    out += f"""                        </tbody>
                    </table></div>
                    <p class="note">Variable names are those printed in Statistics Denmark's researcher variable lists and in the Health Data Authority's extract guide. Names, tables and the years each variable exists differ between the two and change over time, so check the documentation that comes with your own extract.</p>
                    <h4>What to watch out for</h4>
                    <p>{e(L["quality_intro"])}{lpr_refs(L["quality_intro_src"])}</p>
                    <ol class="lpr-points">
"""
    for title, text, src in L["quality"]:
        out += f'                        <li><strong>{e(title)}.</strong> {e(text)}{lpr_refs(src)}</li>\n'
    out += """                    </ol>
                    <h4>Access and linkage</h4>
                    <ul class="lpr-points">
"""
    for title, text, src in L["access"]:
        out += f'                        <li><strong>{e(title)}.</strong> {e(text)}{lpr_refs(src)}</li>\n'
    out += f"""                    </ul>
                    <p class="note">{e(L["access_note"])}</p>
                    <h4>Papers on this site that use it</h4>
                    <p>{len(papers)} of the {len(PAPERS)} papers use the register, and the <a href="codebook.html">Codebook</a> holds {n_defs} of their variable definitions that draw on it. The register goes back to 1977, but the first of these papers is {e(short_cite(first))}. Papers by publication year: {by_period}.</p>
                    <div class="table-wrap"><table class="lpr lpr-papers">
                        <thead><tr><th>Paper</th><th>Journal</th><th>What it takes from the register</th></tr></thead>
                        <tbody>
"""
    for p in sorted(papers, key=lambda p: (-p["year"], p["authors"])):
        ds = use[p["id"]]
        if ds:
            what = "<ul>" + "".join(f'<li>{e(d["variable"])}' + (f' <code>{e(d["codes"])}</code>' if d.get("codes") and len(d["codes"]) <= 90 else "") + "</li>" for d in ds[:4]) + "</ul>"
            if len(ds) > 4:
                what += f'<span class="muted">and {len(ds) - 4} more in the Codebook</span>'
        else:
            src_items = [x for x in p["data"] if re.search(r"\bLPR\b|patient regist|hospital", x, re.I)]
            what = f'<span class="muted">{e(src_items[0])}</span>' if src_items else '<span class="muted">Listed among the paper&rsquo;s data; no definition recorded yet</span>'
        out += (f'                            <tr><td data-label="Paper"><a href="papers.html#{p["id"]}">{e(short_cite(p))}</a><br><span class="t">{e(p["title"])}</span></td>'
                f'<td data-label="Journal">{e(p["journal"])}</td><td data-label="Uses">{what}</td></tr>\n')
    out += """                        </tbody>
                    </table></div>
                    <p class="note">A paper is listed if its data description names the register or if one of its Codebook definitions is built on it. Definitions are quoted from the papers and their replication material.</p>
                    <h4>Sources</h4>
                    <p>The starting point is the article on the register in the <em>Scandinavian Journal of Public Health</em>'s 2011 supplement on Danish registers. Only its abstract is openly available, so most detail on this page comes from the open-access 2015 review by Schmidt and co-authors and from the documentation of the Danish Health Data Authority and Statistics Denmark. Each statement above names its source.</p>
                    <ul class="lpr-sources">
"""
    for k, v in L["sources"].items():
        out += f'                        <li id="src-{k}"><strong>{e(v["short"])}.</strong> {e(v["citation"])} <a href="{e(v["url"])}" target="_blank" rel="noopener">Link</a> <span class="muted">Read: {e(v["read"])}.</span></li>\n'
    out += """                    </ul>
                </details>
"""
    return out


# ---------- home page: three picture cards ----------
def thumb_schools():
    ku, au, _, rows = schools_data()
    top = sorted(rows, key=lambda r: -abs(r[0]))[:5]
    top.sort(key=lambda r: -r[0])
    W, H, x0, bw = 420, 250, 132, 210
    g = f'<svg viewBox="0 0 {W} {H}" role="img" aria-hidden="true">'
    g += f'<rect x="{x0}" y="14" width="10" height="10" rx="2" fill="{NAVY}"/><text x="{x0 + 15}" y="23" font-size="12" fill="#4a5672">Copenhagen</text>'
    g += f'<rect x="{x0 + 110}" y="14" width="10" height="10" rx="2" fill="{SKY}"/><text x="{x0 + 125}" y="23" font-size="12" fill="#4a5672">Aarhus</text>'
    for i, (diff, name, x, y, _) in enumerate(top):
        yy = 46 + i * 40
        a, b = 100 * x / len(ku), 100 * y / len(au)
        label = name.split(",")[0].split(" and ")[0]
        g += f'<text x="{x0 - 10}" y="{yy + 16}" text-anchor="end" font-size="12.5" fill="#1f2a44">{e(label)}</text>'
        g += f'<rect x="{x0}" y="{yy}" width="{max(2, bw * a / 50):.1f}" height="11" rx="2.5" fill="{NAVY}"/><text x="{x0 + max(2, bw * a / 50) + 6:.1f}" y="{yy + 10}" font-size="11.5" fill="#4a5672">{a:.0f}%</text>'
        g += f'<rect x="{x0}" y="{yy + 14}" width="{max(2, bw * b / 50):.1f}" height="11" rx="2.5" fill="{SKY}"/><text x="{x0 + max(2, bw * b / 50) + 6:.1f}" y="{yy + 24}" font-size="11.5" fill="#4a5672">{b:.0f}%</text>'
    return g + "</svg>", max(rows, key=lambda r: abs(r[0])), len(ku), len(au)


def thumb_network():
    """A static picture of the largest connected group of co-authors (spring layout, fixed seed)."""
    import random
    from math import sqrt
    nodes = NETWORK["nodes"]; idx = {n["id"]: i for i, n in enumerate(nodes)}
    adj = {i: set() for i in range(len(nodes))}
    for l in NETWORK["links"]:
        a, b = idx[l["source"]], idx[l["target"]]; adj[a].add(b); adj[b].add(a)
    seen, best = set(), []
    for i in adj:
        if i in seen:
            continue
        comp, stack = [], [i]; seen.add(i)
        while stack:
            u = stack.pop(); comp.append(u)
            for v in adj[u]:
                if v not in seen:
                    seen.add(v); stack.append(v)
        if len(comp) > len(best):
            best = comp
    # Fruchterman-Reingold with a pull to the centre (stronger vertically, so the picture comes out wide);
    # fixed seed, so the picture only changes when the data do
    AR = 1.68
    rnd = random.Random(7); n = len(best); pos = {u: [rnd.uniform(-AR, AR), rnd.uniform(-1, 1)] for u in best}
    k = sqrt(4 * AR / n); iters = 300
    edges = [(u, v) for u in best for v in adj[u] if u < v]
    for it in range(iters):
        temp = 0.25 * (1 - it / iters) ** 1.5 + 0.002
        disp = {u: [-0.9 * pos[u][0] / AR, -0.9 * AR * pos[u][1]] for u in best}
        for a in range(n):
            u = best[a]; pu = pos[u]
            for b in range(a + 1, n):
                v = best[b]; dx, dy = pu[0] - pos[v][0], pu[1] - pos[v][1]
                d2 = dx * dx + dy * dy + 1e-6; f = k * k / d2
                disp[u][0] += dx * f; disp[u][1] += dy * f; disp[v][0] -= dx * f; disp[v][1] -= dy * f
        for u, v in edges:
            dx, dy = pos[u][0] - pos[v][0], pos[u][1] - pos[v][1]
            d = sqrt(dx * dx + dy * dy) + 1e-6; f = d / k
            disp[u][0] -= dx * f; disp[u][1] -= dy * f; disp[v][0] += dx * f; disp[v][1] += dy * f
        for u in best:
            dx, dy = disp[u]; d = sqrt(dx * dx + dy * dy) + 1e-6; step = min(d, temp)
            pos[u][0] += dx / d * step; pos[u][1] += dy / d * step
    xs = [q[0] for q in pos.values()]; ys = [q[1] for q in pos.values()]
    x_lo, x_hi, y_lo, y_hi = min(xs), max(xs), min(ys), max(ys)
    W, H, m = 420, 250, 16
    sx = lambda x: m + (x - x_lo) / (x_hi - x_lo) * (W - 2 * m)
    sy = lambda y: m + (y - y_lo) / (y_hi - y_lo) * (H - 2 * m)
    color = dict(NET_GROUPS)
    g = f'<svg viewBox="0 0 {W} {H}" role="img" aria-hidden="true">'
    g += "".join(f'<line x1="{sx(pos[u][0]):.1f}" y1="{sy(pos[u][1]):.1f}" x2="{sx(pos[v][0]):.1f}" y2="{sy(pos[v][1]):.1f}" stroke="#c9dbe5" stroke-width="0.7"/>' for u, v in edges)
    for u in sorted(best, key=lambda u: len(nodes[u]["papers"])):
        g += f'<circle cx="{sx(pos[u][0]):.1f}" cy="{sy(pos[u][1]):.1f}" r="{2.0 + 1.1 * sqrt(len(nodes[u]["papers"])):.1f}" fill="{color[nodes[u]["group"]]}" stroke="#fff" stroke-width="0.6"/>'
    return g + "</svg>", len(best)


def thumb_lifecycle():
    W, H, x0, x1 = 420, 250, 96, 404
    sx = lambda age: x0 + (x1 - x0) * min(age, 95) / 95
    g = f'<svg viewBox="0 0 {W} {H}" role="img" aria-hidden="true">'
    ages = sorted(ev[1] for ev in LC_EVENTS)
    g += f'<line x1="{x0}" y1="34" x2="{x1}" y2="34" stroke="#c9dbe5" stroke-width="1.2"/>'
    last, row = -99, 0
    for a in ages:
        row = (row + 1) % 3 if sx(a) - last < 11 else 0
        g += f'<circle cx="{sx(a):.1f}" cy="{34 - row * 10}" r="4.6" fill="{NAVY}" stroke="#fff" stroke-width="1.2"/>'
        last = sx(a)
    y = 58
    for group, ls in LC_LANES:
        rows = [sp for _, sp in ls if sp]
        if not rows:
            continue
        g += f'<text x="{x0 - 10}" y="{y + 4 + (len(rows) - 1) * 4.5:.1f}" text-anchor="end" font-size="11" fill="#4a5672">{e(group.split(" and ")[0] if len(group) > 12 else group)}</text>'
        for spans in rows:
            g += "".join(f'<rect x="{sx(a):.1f}" y="{y:.1f}" width="{max(4, sx(b) - sx(a)):.1f}" height="5" rx="2.5" fill="{PALE}"/>' for a, b in spans)
            y += 9
        y += 7
    for a in (0, 20, 40, 60, 80):
        g += f'<text x="{sx(a):.1f}" y="{H - 8}" text-anchor="middle" font-size="11" fill="#76839b">{a}</text>'
    return g + "</svg>", len(LC_EVENTS), len(LC_REG) + 1


def home_hero():
    n_defs = sum(len(p.get("definitions", [])) for p in PAPERS)
    n_regs = len(VARS["individual"]) + len(VARS["firm"])
    stats = [(f"{len(PAPERS):,}", "Papers")]
    panels = ""
    if NETWORK:
        stats.append((f"{len(NETWORK['nodes']):,}", "Authors"))
        s_svg, top, n_ku, n_au = thumb_schools()
        n_svg, n_big = thumb_network()
        l_svg, n_ev, n_reg = thumb_lifecycle()
        a, b = 100 * top[2] / n_ku, 100 * top[3] / n_au
        topic = top[1].split(",")[0].split(" and ")[0]
        tabs = [
            ("network.html", "Network", n_svg, "Author network", f"{len(NETWORK['nodes'])} authors and who they write with. {n_big} of them form one connected group."),
            ("schools.html", "Two schools", s_svg, "Copenhagen vs Aarhus", f"Two universities, two kinds of economics. {topic}: {a:.0f}% of Copenhagen papers, {b:.0f}% of Aarhus papers."),
            ("lifecycle.html", "Life course", l_svg, "Life course", f"{n_ev} events in a life, from birth to death, and the {n_reg} registers that record them."),
        ]
        inputs = "".join(f'<input type="radio" name="explore" id="ex{i}"{" checked" if i == 1 else ""}>' for i in range(1, len(tabs) + 1))
        labels = "".join(f'<label for="ex{i}">{e(t[1])}</label>' for i, t in enumerate(tabs, 1))
        cards = "".join(
            f'\n                <a class="panel p{i}" href="{href}"><span class="panel-fig">{svg}</span><span class="panel-body"><span class="panel-title">{e(title)}</span>'
            f'<span class="panel-text">{e(text)}</span><span class="panel-link">Open the page</span></span></a>'
            for i, (href, _, svg, title, text) in enumerate(tabs, 1))
        panels = f"""            <div class="explore">
                {inputs}
                <div class="explore-head"><span class="explore-label">Explore</span><div class="seg">{labels}</div></div>{cards}
            </div>
"""
    stats += [(f"{n_regs:,}", "Registers"), (f"{n_defs:,}", "Definitions")]
    st = "".join(f'<div><dt>{e(l)}</dt><dd>{v}</dd></div>' for v, l in stats)
    return f"""    <section class="hero">
        <div class="container hero-grid">
            <div class="hero-text">
                <h2 class="hero-title">What have economists learned from <em>Danish registers</em>?</h2>
                <p class="hero-lead">{HOME_INTRO}</p>
                <dl class="stats">{st}</dl>
            </div>
{panels}        </div>
    </section>
"""


# ---------- Chinese edition (zh/) ----------
# The English pages are built first; the Chinese pages are the same HTML with text replaced from a translation table.
# data/zh.json holds interface text ("text": English HTML fragment -> Chinese HTML fragment; "js": string literals in scripts).
# data/papers_zh.json holds each paper's translated summary, variables, period, sample size and sample.
# Anything without a translation stays in English, so a new paper shows up in English until it is translated.
ZH_BLOCK_TAGS = "p|li|ul|ol|div|table|thead|tbody|tr|td|th|h[1-6]|dl|dt|dd|details|summary|section|select|option|label|button|header|footer|nav|title|figcaption"
ZH_LEAF = re.compile(r"<(p|li|h[1-4]|th|td|dt|dd|summary|option|label|title|button|figcaption)\b([^>]*)>((?:(?!<(?:" + ZH_BLOCK_TAGS + r")\b).)*?)</\1>", re.S)
ZH_TEXT = re.compile(r">([^<>]+)<")
ZH_NUM = re.compile(r"\d[\d,.]*\d|\d")
ZH_ATTR = re.compile(r'\b(placeholder|title|aria-label|data-label|alt)="([^"]*)"')
ZH_META = re.compile(r'(<meta (?:name="description"|property="og:title"|property="og:description") content=")([^"]*)(")')


# ---------- Publication analysis: what goes with a Top 5 publication ----------
_PUB = ROOT / "data" / "publication.json"
PUB = json.loads(_PUB.read_text()) if _PUB.exists() else None
# (key, label, how it is measured); a None key starts a block of rows
PUB_ROWS = [
    (None, "Author team", None),
    ("mixed", "Authors in Denmark and abroad", "Some authors based in Denmark and some abroad; the reference group is papers whose authors are all based in Denmark"),
    ("abroad_only", "Authors abroad only", "No author based in Denmark"),
    ("n_authors", "Number of authors", "Count of authors"),
    ("us_author", "Author at a US institution", "At least one author affiliated with a US institution on the paper"),
    ("top_inst", "Author at a leading department", "At least one author at Harvard, Chicago, Berkeley, Princeton, MIT, Stanford, LSE, Yale, Northwestern, Columbia, NYU or UCL"),
    ("ku", "Author at the University of Copenhagen", "At least one author who lists the University of Copenhagen"),
    ("aarhus", "Author at Aarhus University", "At least one author who lists Aarhus University"),
    ("sen_max", "Seniority of the most senior author", "Years between that author's first publications in OpenAlex and the paper's year"),
    ("sen_min", "Seniority of the most junior author", "Same measure for the author who started most recently"),
    (None, "Paper", None),
    ("year", "Publication year", "Year of publication minus 2015"),
    ("firm", "Firm-level data", "The paper uses firm-level registers, alone or with individual-level ones"),
    ("log_n", "Sample size (log10)", "Base-10 logarithm of the largest sample size reported on the Data &amp; samples page"),
    ("log_n_miss", "Sample size not reported", "Sample size missing; the median is used in its place"),
    ("span", "Years of data", "Length of the data period in years"),
    ("n_data", "Number of datasets", "Datasets listed for the paper on this site"),
    ("dk_title", "Denmark in the title", "The title contains Denmark or Danish"),
    ("survey", "Linked survey", "The paper links a survey to the registers"),
    ("repl_pkg", "Replication package", "A public replication package is listed"),
    ("nber_wp", "NBER working paper", "A version of the paper appeared as an NBER working paper"),
    ("log_cites", "Citations (log)", "Natural logarithm of one plus the OpenAlex citation count in November 2026"),
    ("cites_miss", "Citations not found", "No OpenAlex record matched; the median is used in its place"),
    ("has_ra", "Thanks research assistants", "The acknowledgments thank at least one person for research assistance"),
    (None, "Themes", None),
    ("th_taxation", "Taxation", "Theme on this site"), ("th_household-finance", "Household finance", "Theme on this site"),
    ("th_labor", "Labour", "Theme on this site"), ("th_health", "Health", "Theme on this site"), ("th_family", "Family", "Theme on this site"),
    ("th_firms", "Firms", "Theme on this site"), ("th_children", "Children", "Theme on this site"),
]


def build_publication():
    ms = PUB["models"]
    stars = lambda p: "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
    num = lambda x: ("&minus;" if x < 0 else "") + f"{abs(x):.3f}"

    def cell(m, k):
        c = m["coef"].get(k)
        if not c:
            return "<td></td>"
        st = stars(c["p"])
        return (f'<td{" class=\"sig\"" if st else ""}><span class="est">{num(c["b"])}</span>'
                + (f'<span class="stars">{st}</span>' if st else "") + f'<span class="se">({c["se"]:.3f})</span></td>')

    out = head(
        "Publication analysis | Beautiful Danish Data",
        "Which features of a Danish register paper go with publication in a Top 5 journal: coefficient charts from a logit regression on author team, institutions, data, seniority and citations.",
        "publication.html",
    )
    out += nav("publication.html")
    m5 = ms[4]
    # full table, kept behind a disclosure as the table view of the charts
    full = f"""                <table class="regtable">
                    <thead><tr><th></th>{"".join(f'<th>{m["num"]}<span class="mlabel">{e(m["label"])}</span></th>' for m in ms)}</tr></thead>
                    <tbody>
"""
    for k, label, _ in PUB_ROWS:
        if k is None:
            full += f'                        <tr class="rgroup"><td colspan="{len(ms) + 1}">{label}</td></tr>\n'
        else:
            full += f'                        <tr><td>{label}</td>{"".join(cell(m, k) for m in ms)}</tr>\n'
    full += "                    </tbody>\n                </table>\n"
    foot = [("Papers", lambda m: str(m["n"])), ("Top 5 papers", lambda m: str(m["top5"])), ("Pseudo R&sup2;", lambda m: f'{m["r2"]:.3f}'),
            ("Cross-validated AUC", lambda m: f'{m["auc"]:.3f}'), ("Cross-validated accuracy", lambda m: f'{100 * m["acc"]:.1f}%'),
            ("Accuracy of always guessing not Top 5", lambda m: f'{100 * m["base"]:.1f}%')]

    # coefficient charts: one per block of variables, one line per specification the variable enters
    LO, HI, TICKS = -0.5, 0.6, (-0.4, -0.2, 0.0, 0.2, 0.4)
    pos = lambda x: 100 * (min(max(x, LO), HI) - LO) / (HI - LO)
    grid = ", ".join(f"linear-gradient({'var(--secondary-color)' if t == 0 else 'var(--border-color)'}, {'var(--secondary-color)' if t == 0 else 'var(--border-color)'}) {pos(t):.2f}% 0 / 1px 100% no-repeat" for t in TICKS)
    axis = ('<div class="cf-axis" aria-hidden="true"><span></span><span></span><div class="cf-ticks">'
            + "".join(f'<span style="left:{pos(t):.2f}%">{"0" if t == 0 else ("&minus;" if t < 0 else "+") + f"{abs(t):.1f}"}</span>' for t in TICKS) + "</div></div>\n")

    def chart(rows):
        h = f'            <div class="coef" style="--grid: {grid}">\n                {axis}'
        for k, label in rows:
            h += f'                <div class="cv"><div class="cv-name">{label}</div><div class="cv-rows">'
            for m in ms:
                c = m["coef"].get(k)
                if not c:
                    continue
                lo, hi = c["b"] - 1.96 * c["se"], c["b"] + 1.96 * c["se"]
                sig = lo > 0 or hi < 0
                tip = f'{m["num"]} {m["label"]}: {"−" if c["b"] < 0 else ""}{abs(c["b"]):.3f} (SE {c["se"]:.3f}), p = {c["p"]:.3f}'
                h += (f'<div class="cr{" sig" if sig else ""}" title="{e(tip)}"><span class="sp">{m["num"]}</span><div class="track">'
                      f'<i class="ci" style="left:{pos(lo):.2f}%;width:{pos(hi) - pos(lo):.2f}%"></i><i class="dot" style="left:{pos(c["b"]):.2f}%"></i></div></div>')
            h += "</div></div>\n"
        return h + f"                {axis}            </div>\n"

    blocks, cur = [], None
    for k, label, _ in PUB_ROWS:
        if k is None:
            cur = (label, []); blocks.append(cur)
        elif not k.endswith("_miss"):
            cur[1].append((k, label))

    out += f"""    <section class="section intro">
        <div class="container">
            <h2 class="section-title">What goes with a Top 5 publication</h2>
            <p>Of the {PUB["n_papers"]} papers on this site, {PUB["n_top5"]} appeared in a Top 5 journal. The charts ask which features of a paper go with being one of them. Papers with an author at a leading department, with larger samples and with more citations are more often in the Top 5. The seniority of the authors makes no detectable difference.</p>
            <p>Each line is one estimate: the dot is the change in the probability of a Top 5 publication that goes with the variable, and the bar is its 95% confidence interval. A variable has one line for every specification it enters, numbered as below. Each specification adds variables to the one before.</p>
            <ul class="cf-specs">{"".join(f'<li><b>{m["num"]}</b> {e(m["label"])}</li>' for m in ms)}</ul>
            <p class="cf-key"><span class="k"><span class="cr sig"><span class="track"><i class="ci" style="left:0;width:100%"></i><i class="dot" style="left:50%"></i></span></span> <span>Interval excludes zero</span></span><span class="k"><span class="cr"><span class="track"><i class="ci" style="left:0;width:100%"></i><i class="dot" style="left:50%"></i></span></span> <span>Interval includes zero</span></span></p>
"""
    for label, rows in blocks:
        out += f'            <h3 class="cf-title">{label}</h3>\n' + chart(rows)
    out += f"""            <p class="note">Logit regressions; the outcome is one if the paper appeared in a Top 5 journal. Estimates are average marginal effects on a common scale, so 0.2 means 20 percentage points. Hover over a line for the numbers. The two indicators for a missing sample size and a missing citation count are in the regressions but not drawn. Specification (6) covers only the papers whose full text could be read, because the research-assistant variable comes from the acknowledgments.</p>
            <h3 class="cf-title">Fit</h3>
            <div class="table-wrap">
                <table class="regtable fit">
                    <thead><tr><th></th>{"".join(f'<th>{m["num"]}<span class="mlabel">{e(m["label"])}</span></th>' for m in ms)}</tr></thead>
                    <tbody>
"""
    for label, fn in foot:
        out += f'                        <tr class="rfit"><td>{label}</td>{"".join(f"<td>{fn(m)}</td>" for m in ms)}</tr>\n'
    out += f"""                    </tbody>
                </table>
            </div>
            <p class="note">The cross-validated figures are averages over 20 repetitions of five-fold cross-validation; an AUC of 0.5 is no better than chance.</p>
            <details class="net-all"><summary>The same estimates as a table</summary>
            <div class="table-wrap">
{full}            </div>
            <p class="note">Average marginal effects with standard errors in parentheses. * <em>p</em> &lt; 0.10, ** <em>p</em> &lt; 0.05, *** <em>p</em> &lt; 0.01.</p>
            </details>
        </div>
    </section>
    <section class="section">
        <div class="container">
            <h2 class="section-title">How to read it</h2>
            <p>These are associations within a selected group, not causes. Every paper here was already published in a good journal, so the comparison is Top 5 against other good journals. Citations are counted after publication and a Top 5 publication itself brings citations, so column (5) describes the papers and does not predict anything in advance. Replication packages are required by the Top 5 journals, so that row may also reflect the outcome.</p>
            <p>The models predict poorly. Column (5) classifies {100 * m5["acc"]:.1f}% of papers correctly out of sample, against {100 * m5["base"]:.1f}% for always guessing that a paper is not in the Top 5.</p>
            <div class="table-wrap">
                <table class="regvars">
                    <thead><tr><th>Variable</th><th>Other journals</th><th>Top 5</th><th>How it is measured</th></tr></thead>
                    <tbody>
"""
    for k, label, how in PUB_ROWS:
        if k is None:
            continue
        a, b = PUB["means"][k]
        out += f'                        <tr><td>{label}</td><td>{a:.2f}</td><td>{b:.2f}</td><td>{how}</td></tr>\n'
    out += f"""                    </tbody>
                </table>
            </div>
            <p class="note">Means by group; for yes-or-no variables the mean is the share of papers. The median paper outside the Top 5 has {PUB["median_cites"][0]:.0f} citations and the median Top 5 paper {PUB["median_cites"][1]:.0f}. Author locations come from the affiliations on each paper in OpenAlex where available, and otherwise from the <a href="network.html">Author network</a> page; the leading-department, Copenhagen and Aarhus variables use every institution listed for an author on that page. Seniority is missing for a few authors with no OpenAlex profile and is then taken over the remaining authors. The data and the script are in the <code>analysis</code> folder on <a href="https://github.com/Zhurt0/beautiful-danish-data" target="_blank" rel="noopener">GitHub</a>.</p>
        </div>
    </section>
"""
    out += FOOTER
    return out


# ---------- Authors and research assistants ----------
_ARA = ROOT / "data" / "authors_ra.json"
ARA = json.loads(_ARA.read_text()) if _ARA.exists() else None
ARA_GROUP = {"top5": "Top 5", "aeri": "AER: Insights", "aej": "AEJ", "restat": "REStat", "ej": "Economic Journal", "jole": "JOLE", "jpube": "JPubE", "all": "All papers"}
ARA_TEAM = ["Authors in Denmark only", "Authors in Denmark and abroad", "Authors abroad only"]
ARA_CAT = {"academic faculty": "Faculty position", "postdoc": "Postdoc", "PhD student": "PhD student",
           "PhD completed, later position not found": "PhD completed, position not found",
           "central bank / government / intl org": "Central bank, government or international organisation",
           "research institute / think tank": "Research institute", "private sector": "Private sector",
           "still a pre-doctoral RA": "Still a research assistant", "unknown": "Not found"}


def build_authors():
    A, R = ARA["author"], ARA["ra"]
    pct = lambda x, n: 100 * x / n if n else 0

    def stacked(rows, label_of):
        h = '            <div class="stk">\n'
        for key, *vals in rows:
            n = sum(vals)
            segs = "".join(
                f'<i class="s{i}" style="width:{pct(v, n):.2f}%" title="{v} of {n} papers">{f"<b{' class=nar' if pct(v, n) < 16 else ''}>{pct(v, n):.0f}%</b>" if pct(v, n) >= 7 else ""}</i>'
                for i, v in enumerate(vals) if v)
            h += (f'                <div class="stk-row{" total" if key == "all" else ""}"><span class="stk-label">{e(label_of(key))}</span>'
                  f'<span class="stk-bar">{segs}</span><span class="stk-n">{n}</span></div>\n')
        return h + "            </div>\n"

    def counts_table(rows, label_of, first):
        h = f'<table class="regvars cnt"><thead><tr><th>{first}</th>' + "".join(f"<th>{t}</th>" for t in ARA_TEAM) + "<th>Papers</th></tr></thead><tbody>"
        for key, *vals in rows:
            h += f"<tr><td>{e(label_of(key))}</td>" + "".join(f"<td>{v}</td>" for v in vals) + f"<td>{sum(vals)}</td></tr>"
        return h + "</tbody></table>"

    legend = '<p class="stk-key">' + "".join(f'<span class="k"><i class="s{i}"></i><span>{t}</span></span>' for i, t in enumerate(ARA_TEAM)) + "</p>"
    tot = A["by_group"][-1]; n_all = sum(tot[1:])
    t5 = A["by_group"][0]; jp = next(r for r in A["by_group"] if r[0] == "jpube")
    out = head(
        "Authors and research assistants | Beautiful Danish Data",
        "How many Danish register papers are written with researchers outside Denmark, which papers thank research assistants, and where those assistants went next.",
        "authors.html",
    )
    out += nav("authors.html")
    out += f"""    <section class="section intro">
        <div class="container">
            <h2 class="section-title">Most papers are written with someone abroad</h2>
            <p>Of the {n_all} papers on this site, {tot[2] + tot[3]} ({pct(tot[2] + tot[3], n_all):.0f}%) have at least one author based outside Denmark, and {tot[1]} ({pct(tot[1], n_all):.0f}%) are written entirely by authors based in Denmark. Teams based only in Denmark are rare in the Top 5 ({t5[1]} of {sum(t5[1:])} papers) and common in the Journal of Public Economics ({jp[1]} of {sum(jp[1:])}).</p>
            <h3 class="cf-title">By journal</h3>
            {legend}
{stacked(A["by_group"], lambda k: ARA_GROUP[k])}            <h3 class="cf-title">By year of publication</h3>
            {legend}
{stacked(A["by_period"], lambda k: k)}            <p class="note">Share of papers by where the authors are based; the number on the right is the count of papers. Based means the institution an author works at, not nationality, so a Danish economist at a university abroad counts as abroad. For {A["basis"]["per-paper"]} papers the locations are the affiliations on that paper in OpenAlex; for the other {A["basis"]["author-level"]} they are the author's usual institution on the <a href="network.html">Author network</a> page.</p>
            <details class="net-all"><summary>The same numbers as a table</summary>
            <div class="table-wrap">{counts_table(A["by_group"], lambda k: ARA_GROUP[k], "Journal")}</div>
            <div class="table-wrap">{counts_table(A["by_period"], lambda k: k, "Published")}</div>
            </details>
        </div>
    </section>
"""
    known = R["n_ra"] - dict(R["cats"])["unknown"]
    cmax = max(v for _, v in R["cats"])
    bars = "".join(
        f'                <div class="hb-row{" none" if k == "unknown" else ""}"><span class="hb-label">{ARA_CAT[k]}</span>'
        f'<span class="hb-track"><i style="width:{100 * v / cmax:.1f}%"></i><b>{v}</b></span></div>\n' for k, v in R["cats"])
    tm = {k: (n, x) for k, n, x in R["by_team"]}
    g_rows = "".join(f'<tr><td>{e(ARA_GROUP[g])}</td><td>{n}</td><td>{x}</td><td>{pct(x, n):.0f}%</td><td>{k}</td></tr>' for g, n, x, k in R["by_group"])
    later = ""
    for l in sorted(R["later"], key=lambda l: -len(l["papers"])):
        rp = PAPER_BY_ID[l["ra_paper"]]
        links = ", ".join(f'<a href="papers.html#{pid}">{e(short_cite(PAPER_BY_ID[pid]))}</a>' for pid in l["papers"] if pid in PAPER_BY_ID and pid != rp["id"])
        mid = " was thanked in an early version of " if rp["id"] in l["papers"] else " was thanked in "
        end = " became one of its authors, and is also an author of " if rp["id"] in l["papers"] else " and is an author of "
        later += f'                <li><strong>{e(l["name"])}</strong>{mid}<a href="papers.html#{rp["id"]}">{e(short_cite(rp))}</a>,{end}{links}.</li>\n'
    out += f"""    <section class="section">
        <div class="container">
            <h2 class="section-title">Research assistants and where they went</h2>
            <p>The acknowledgments of {R["n_papers"]} papers thank someone for research assistance, out of the {R["n_pdf"]} whose full text could be read. They name {R["n_ra"]} people. A web search found what {known} of them did next: most went on to a PhD, and many are now on a university faculty.</p>
            <div class="tiles">
                <div class="tile"><b>{R["n_papers"]}</b><span>papers thank research assistants</span></div>
                <div class="tile"><b>{R["n_ra"]}</b><span>people thanked</span></div>
                <div class="tile"><b>{R["n_phd"]}</b><span>went on to a PhD, finished or in progress</span></div>
                <div class="tile"><b>{len(R["later"])}</b><span>later wrote a paper on this site</span></div>
            </div>
            <h3 class="cf-title">Where they are now</h3>
            <div class="hb">
{bars}            </div>
            <p class="note">Latest position found for each of the {R["n_ra"]} people, from university pages, personal sites and publication records. The search relied on search results and could not open most pages, so some positions may be out of date. People who were not found are mostly student assistants in Denmark with no public profile; that says nothing about how they fared, and it tilts the picture towards academia. Names and individual positions are not published here.</p>
            <h3 class="cf-title">Which papers thank research assistants</h3>
            <p>Thanks for research assistance are concentrated in the Top 5 and in papers written across borders: {tm["Mixed"][1]} of the {tm["Mixed"][0]} papers with authors in Denmark and abroad thank an assistant ({pct(tm["Mixed"][1], tm["Mixed"][0]):.0f}%), against {tm["DK only"][1]} of {tm["DK only"][0]} with authors in Denmark only and {tm["Abroad only"][1]} of {tm["Abroad only"][0]} with authors abroad only.</p>
            <div class="table-wrap">
                <table class="regvars cnt">
                    <thead><tr><th>Journal</th><th>Papers read</th><th>Thank assistants</th><th>Share</th><th>People thanked</th></tr></thead>
                    <tbody>{g_rows}</tbody>
                </table>
            </div>
            <p class="note">Most of the texts read are working-paper versions, whose acknowledgments can differ from the published ones. A person thanked in two papers is counted in both rows.</p>
            <h3 class="cf-title">From research assistant to author</h3>
            <ul class="plain ra-later">
{later}            </ul>
        </div>
    </section>
"""
    out += FOOTER
    return out


def zh_col(s):
    return re.sub(r"\s+", " ", s).strip()


def zh_norm(s):
    """Replace numbers outside tags with {0}, {1}, ... so that counts in interface sentences can change."""
    nums, out = [], []
    for part in re.split(r"(<[^>]+>)", s):
        if part.startswith("<"):
            out.append(part)
        else:
            out.append(ZH_NUM.sub(lambda m: (nums.append(m.group(0)), "{%d}" % (len(nums) - 1))[1], part))
    return "".join(out), nums


def zh_get(tm, s):
    key = zh_col(s)
    if not key or not re.search(r"[A-Za-z]", key):
        return None
    if key in tm:
        return tm[key]
    nkey, nums = zh_norm(key)
    if nums and nkey in tm:
        out = tm[nkey]
        for i, n in enumerate(nums):
            out = out.replace("{%d}" % i, n)
        return out
    return None


def zh_table():
    tm, js = {}, {}
    f = ROOT / "data" / "zh.json"
    if f.exists():
        d = json.loads(f.read_text())
        tm.update({zh_col(k): v for k, v in d.get("text", {}).items()}); js.update(d.get("js", {}))
    f = ROOT / "data" / "papers_zh.json"
    if f.exists():
        pz = json.loads(f.read_text())
        for p in PAPERS:
            z = pz.get(p["id"])
            if not z:
                continue
            for k in ("summary", "period", "sample_size", "sample"):
                if p.get(k) and z.get(k):
                    tm[zh_col(e(p[k]))] = e(z[k])
            if p.get("variables") and len(z.get("variables", [])) == len(p["variables"]):
                for en, zh in zip(p["variables"], z["variables"]):
                    tm[zh_col(e(en))] = e(zh)
    return tm, js


def zh_page(page, src, tm, js):
    def keep_ws(orig, new):
        return orig[:len(orig) - len(orig.lstrip())] + new + orig[len(orig.rstrip()):]

    def block(m):
        z = zh_get(tm, m.group(3))
        return m.group(0) if z is None else f"<{m.group(1)}{m.group(2)}>{keep_ws(m.group(3), z)}</{m.group(1)}>"

    def text(m):
        z = zh_get(tm, m.group(1))
        return m.group(0) if z is None else ">" + keep_ws(m.group(1), z) + "<"

    def attr(m):
        z = zh_get(tm, m.group(2))
        return m.group(0) if z is None else f'{m.group(1)}="{re.sub("<[^>]+>", "", z)}"'

    def script(m):
        body = m.group(2)

        def dq(q):                      # JSON payload values
            try:
                raw = json.loads(q.group(0))
            except ValueError:
                return q.group(0)
            z = zh_get(tm, e(raw)) if isinstance(raw, str) else None
            return q.group(0) if z is None else json.dumps(keep_ws(raw, html.unescape(re.sub("<[^>]+>", "", z))), ensure_ascii=False).replace("</", "<\\/")

        def sq(q):                      # interface strings written in the script itself
            inner = q.group(1)
            z = js.get(inner.strip())
            return q.group(0) if z is None else "'" + keep_ws(inner, z).replace("'", "\\'") + "'"

        body = re.sub(r'"(?:[^"\\\n]|\\.)*"', dq, body)
        body = re.sub(r"'((?:[^'\\\n]|\\.)*)'", sq, body)
        body = ZH_TEXT.sub(text, body)
        return m.group(1) + body + m.group(3)

    parts = re.split(r"(<script\b[^>]*>.*?</script>)", src, flags=re.S)
    for i, part in enumerate(parts):
        if part.startswith("<script"):
            parts[i] = re.sub(r"(<script\b[^>]*>)(.*?)(</script>)", script, part, flags=re.S)
        else:
            part = ZH_META.sub(lambda m: m.group(1) + (re.sub("<[^>]+>", "", zh_get(tm, m.group(2)) or m.group(2))) + m.group(3), part)
            part = ZH_LEAF.sub(block, part)
            part = ZH_TEXT.sub(text, part)
            parts[i] = ZH_ATTR.sub(attr, part)
    out = "".join(parts)
    out = out.replace('<html lang="en">', '<html lang="zh-Hans">', 1)
    out = out.replace(f'<link rel="canonical" href="{SITE}', f'<link rel="canonical" href="{SITE}zh/', 1)
    out = out.replace(f'<meta property="og:url" content="{SITE}', f'<meta property="og:url" content="{SITE}zh/', 1)
    out = out.replace('<meta property="og:site_name" content="Beautiful Danish Data">', '<meta property="og:site_name" content="Beautiful Danish Data">\n    <meta property="og:locale" content="zh_CN">', 1)
    # no Google Fonts on the Chinese pages (not reachable everywhere); system serif fonts are set in the stylesheet
    out = re.sub(r'\s*<link rel="preconnect" href="https://fonts\.g[^>]*>', "", out)
    out = re.sub(r'\s*<link href="https://fonts\.googleapis\.com[^>]*>', "", out)
    out = out.replace('src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"', 'src="../vendor/d3.min.js"')
    out = re.sub(r'(?<=["\'(])(css|files|vendor)/', r"../\1/", out)
    sw_en = f'<p class="lang-switch"><span class="cur">EN</span><a href="zh/{page}" lang="zh-Hans" hreflang="zh-Hans">中文</a></p>'
    assert sw_en in out, page
    out = out.replace(sw_en, f'<p class="lang-switch"><a href="../{page}" lang="en" hreflang="en">EN</a><span class="cur">中文</span></p>')
    return out


def build_zh(pages):
    tm, js = zh_table()
    if not tm:
        return 0
    (ROOT / "zh").mkdir(exist_ok=True)
    for page, src in pages.items():
        (ROOT / "zh" / page).write_text(zh_page(page, src, tm, js))
    missing = [p["id"] for p in PAPERS if zh_col(e(p["summary"])) not in tm]
    if missing:
        print(f"zh: {len(missing)} papers have no Chinese summary and are shown in English: {', '.join(missing[:8])}{' ...' if len(missing) > 8 else ''}")
    return len(pages)


def sitemap(pages, with_zh):
    """Every page, with its Chinese twin as an alternate, for submission in Google Search Console."""
    out = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    for name in pages:
        path = "" if name == "index.html" else name
        alts = f'    <xhtml:link rel="alternate" hreflang="en" href="{SITE}{path}"/>\n    <xhtml:link rel="alternate" hreflang="zh-Hans" href="{SITE}zh/{path}"/>\n' if with_zh else ""
        for loc in [SITE + path] + ([SITE + "zh/" + path] if with_zh else []):
            out += f"  <url>\n    <loc>{loc}</loc>\n{alts}  </url>\n"
    return out + "</urlset>\n"


if __name__ == "__main__":
    built = {
        "index.html": build_index(), "papers.html": build_papers(), "themes.html": build_themes(), "variables.html": build_variables(),
        "samples.html": build_samples(), "lifecycle.html": build_lifecycle(), "codebook.html": build_codebook(),
        "survey.html": build_survey(),
    }
    if NETWORK:
        built["network.html"] = build_network(); built["schools.html"] = build_schools()
    if PUB:
        built["publication.html"] = build_publication()
    if ARA:
        built["authors.html"] = build_authors()
    for name, src in built.items():
        (ROOT / name).write_text(src)
    n_zh = build_zh(built)
    (ROOT / "sitemap.xml").write_text(sitemap(built, n_zh))
    print(f"built {len(built)} pages from {len(PAPERS)} papers and {len(VARS['individual']) + len(VARS['firm'])} registers" + (f", plus {n_zh} Chinese pages in zh/" if n_zh else ""))
