# Beautiful Danish Data

A field guide to economics published with Danish administrative register data.

Live site: https://zhurt0.github.io/beautiful-danish-data/

Three pages:

1. **Summary** (`index.html`): one-paragraph summaries of papers in the Top 5 journals, the *American Economic Journals* (Applied and Policy), the *Review of Economics and Statistics* and the *Economic Journal* that are built on Danish registers, grouped by journal.
2. **Themes** (`themes.html`): the same papers regrouped by topic (taxation, household finance, labour, trade, family, health, migration, crime, children, inequality).
3. **Variable map** (`variables.html`): the Statistics Denmark registers and variables behind those papers, at the individual level and at the firm level, with a short guide to linking the two sides.

## Editing

All content lives in two JSON files. The HTML pages are generated from them.

- `data/papers.json`: one object per paper with `authors`, `year`, `journal`, `group` (`top5`, `aej`, `restat`, `ej`), `title`, `summary`, `themes`, `data` and `level` (`individual`, `firm`, `both`).
- `data/variables.json`: registers under `individual` and `firm`, each with a short description, a list of `[variable, meaning]` pairs and the ids of papers that use it.

After editing, regenerate the pages and commit everything:

```sh
python3 build.py
git add -A && git commit -m "Add <paper>" && git push
```

Theme keys and names are defined in `build.py`.

## Contributing

The list is curated and far from complete. Pull requests that add a paper, fix a summary or correct a variable name are welcome. Please keep summaries to a few sentences and name the registers the paper actually uses.

## Deployment

GitHub Pages serves the repository root from the `main` branch through the workflow in `.github/workflows/pages.yml`.

## License

Text is released under CC BY 4.0. Summaries are the maintainer's own reading of each paper; always cite the original.
