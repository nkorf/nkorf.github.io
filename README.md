# nkorf.github.io

Personal academic website of Prof. Nikolaos Korfiatis, built with Hugo and the
HugoBlox Academic CV kit.

## Where the content lives

| Content | Source |
|---|---|
| Publications, clinical trials, policy citations, CV PDF, photo | [nkorf/nkorf](https://github.com/nkorf/nkorf), pulled at build time by `scripts/sync_profile.py` |
| Profile, education, appointments | `data/authors/me.yaml` |
| Home page | `content/_index.md` |
| News, press clippings, supervision, teaching, notes | `content/*.md`, `content/notes/` |

Generated files (`content/publications/<key>/`, `content/clinical-trials.md`,
`content/policy-citations.md`, `static/uploads/korfiatis_cv.pdf`,
`assets/media/authors/me.jpg`) are not committed.

To add a publication, edit `publications.bib` in `nkorf/nkorf`. The site picks
it up at the next daily build, or at once via *Actions → Build and deploy site →
Run workflow*.

## Local build

```bash
npm ci
python3 scripts/sync_profile.py --profile ../nkorf --site .
hugo server
```

Requires Hugo extended 0.166 or later, Go and Node. `hugo.yaml` allows Hugo to
run `tailwindcss` (`security.exec.allow`).

## Overrides

`layouts/_partials/hbx/blocks/` overrides two HugoBlox blocks to print the
postnominals (FRSA, FHEA) and the name prefix, and to hide the education and
interest cards on the home page.
