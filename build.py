#!/usr/bin/env python3
"""Generate the static pages of Beautiful Danish Data from data/*.json.

Run `python3 build.py` after editing data/papers.json or data/variables.json.
"""
import html
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
    ("aej", "AEJ: Applied and AEJ: Policy", "American Economic Journal: Applied Economics and American Economic Journal: Economic Policy."),
    ("restat", "Review of Economics and Statistics", ""),
    ("ej", "Economic Journal", ""),
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
    items = [("index.html", "Summary"), ("themes.html", "Themes"), ("variables.html", "Variable map")]
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


def paper_card(p, show_themes=True):
    themes = ""
    if show_themes:
        themes = '<p class="tags">' + " ".join(
            f'<a class="tag" href="themes.html#{t}">{e(THEME_NAME[t])}</a>' for t in p["themes"]
        ) + "</p>"
    data = ", ".join(e(d) for d in p["data"])
    return f"""                <article class="paper" id="{p['id']}">
                    <h4><a href="{scholar(p['title'])}" target="_blank" rel="noopener">{e(p['title'])}</a></h4>
                    <p class="meta">{e(p['authors'])} &middot; <em>{e(p['journal'])}</em>, {p['year']} &middot; <span class="level">{LEVEL_LABEL[p['level']]}</span></p>
                    <p class="summary">{e(p['summary'])}</p>
                    <p class="data"><strong>Data:</strong> {data}</p>
{themes}
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
            <p>Denmark links every resident, firm, hospital visit, tax return and job to a single identifier, and lets researchers work with the whole population from the 1980s onwards. This page is a reading list of the economics that has come out of that infrastructure in the top general-interest journals: what question each paper asks, what it finds, and which registers it is built from.</p>
            <p>The list is curated, not exhaustive. It covers {len(PAPERS)} papers so far. The <a href="themes.html">Themes</a> page regroups the same papers by topic, and the <a href="variables.html">Variable map</a> lists the registers and variables they rely on, at the individual and the firm level. If a paper is missing or a summary is wrong, open an issue or a pull request on GitHub.</p>
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


if __name__ == "__main__":
    (ROOT / "index.html").write_text(build_index())
    (ROOT / "themes.html").write_text(build_themes())
    (ROOT / "variables.html").write_text(build_variables())
    print(f"built 3 pages from {len(PAPERS)} papers and {len(VARS['individual']) + len(VARS['firm'])} registers")
