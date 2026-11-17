# Beautiful Danish Data

A field guide to economics published with Danish administrative register data.

Live site: https://zhurt0.github.io/beautiful-danish-data/

Ten pages, each also in Chinese under `zh/`. The header shows the five main pages and puts the rest under "More":

1. **Summary** (`index.html`): a short front page with the headline figures, a three-tab preview (Author network, Copenhagen vs Aarhus, Life course) whose small pictures are drawn from the data at build time, and the way into the papers by journal.
1. **Papers** (`papers.html`): one-paragraph summaries of papers in the Top 5 journals, the *American Economic Journals* (Applied and Policy), the *Review of Economics and Statistics*, the *Economic Journal*, the *Journal of Labor Economics* and the *Journal of Public Economics* that are built on Danish registers, grouped by journal, with the note on how the papers were selected.
1. **Themes** (`themes.html`): the same papers regrouped by topic (taxation, household finance, labour, trade, family, health, migration, crime, children, inequality).
1. **Data & samples** (`samples.html`): one sortable table with each paper's data period, sample size, level and datasets.
1. **Life course** (`lifecycle.html`): the main events in a person's life from birth to death, by typical age, and the registers that record each one, with what they record and how many papers use them.
1. **Codebook** (`codebook.html`): how each paper defines its key variables, with register names and codes, taken from the paper, its online appendix or its replication code.
1. **Survey** (`survey.html`): the surveys linked to the registers in these papers, with questionnaires and codebooks. Statistics Denmark questionnaires are mirrored under `files/surveys/` with their SHA-256; other owners' documents are linked, not copied.
1. **Variable map** (`variables.html`): the Statistics Denmark registers and variables behind those papers, at the individual level and at the firm level, with a short guide to linking the two sides. The National Patient Register (LPR) entry opens into a longer account: history, what a record contains, tables and variables, pitfalls, access, and the papers on this site that use it. That text lives in `data/lpr.json`, where every statement names its source.
1. **Author network** (`network.html`): who wrote with whom, coloured by where each author was based, with tables of the most frequent pairs, institutions and all authors.
1. **Copenhagen vs Aarhus** (`schools.html`): how the themes of papers with University of Copenhagen authors differ from those with Aarhus University authors, with Fisher exact tests; computed from `data/papers.json` and `data/network.json` at build time.

## Editing

All content lives in JSON files under `data/`. The HTML pages are generated from them.

- `data/papers.json`: one object per paper with `authors`, `year`, `journal`, `group` (`top5`, `aeri`, `aej`, `restat`, `ej`, `jole`, `jpube`), `title`, `summary`, `themes`, `data` (datasets used), `level` (`individual`, `firm`, `both`), and where known `variables` (key variables and their role), `period`, `sample_size`, `sample` (who is in the sample), `sample_source` (where these facts were read) and `sample_confidence` (`paper` if read from the paper or its working-paper version, `abstract` if only from an abstract).
- Sample facts were extracted from each paper's data section, usually the open working-paper version, so published figures can differ slightly. Missing figures are left blank, never estimated.
- `definitions` in `data/papers.json` hold the Codebook entries (`concept`, `variable`, `definition`, `registers`, `codes` and where each was found).
- `data/surveys.json`: one object per survey with its owner, documents (and a `mirror` record for copies on this site) and the papers that use it.
- `data/network.json`: authors (`name`, `papers`, `primary` and all `institutions` as listed on these papers in OpenAlex, colour `group`) and co-author `links` with the joint papers. Research networks such as NBER, CEPR, IZA and CESifo are dropped from affiliations.
- `data/variables.json`: registers under `individual` and `firm`, each with a short description, a list of `[variable, meaning]` pairs and the ids of papers that use it.

After editing, regenerate the pages and commit everything:

```sh
python3 build.py
git add -A && git commit -m "Add <paper>" && git push
```

Theme keys and names are defined in `build.py`.

## Chinese edition

`python3 build.py` also writes a Chinese copy of every page to `zh/`. The Chinese pages are the English pages with text replaced from two files, so the two editions cannot drift apart in structure:

- `data/papers_zh.json`: for each paper id, the Chinese `summary`, `variables` (same number of items, same order as in `data/papers.json`), `period`, `sample_size` and `sample`.
- `data/zh.json`: interface text. `text` maps an English fragment exactly as it appears in the generated HTML (tags and entities included) to its Chinese version; numbers may be written as `{0}`, `{1}`, ... so that counts can change. `js` maps string literals used inside the page scripts.

Paper titles, authors, journals, dataset names and the Codebook definitions stay in the original language. Anything without a translation is shown in English, and the build prints the ids of papers that still lack a Chinese summary. If an English sentence is edited, its entry in these files has to be updated too. The Chinese pages use system fonts and a local copy of D3 (`vendor/d3.min.js`) instead of Google Fonts and a CDN.

## Contributing

The Summary page states how the papers were selected (journals, period, search, inclusion rules); the journal counts and year range in that box are computed from `data/papers.json`, and the wording lives in `build.py`.

The list is curated and far from complete. Pull requests that add a paper, fix a summary or correct a variable name are welcome. Please keep summaries to a few sentences and name the registers the paper actually uses.

## Deployment

GitHub Pages serves the repository root from the `main` branch through the workflow in `.github/workflows/pages.yml`.

## License

Text is released under CC BY 4.0. Summaries are the maintainer's own reading of each paper; always cite the original.
