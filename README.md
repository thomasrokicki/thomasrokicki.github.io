# thomasrokicki-github.io
Personnal website

- `public/` is the website root: the only directory the web server exposes.
- `cv/data.yaml` holds the profile, publications, talks, positions and education.
  Run `make` (needs Python 3 with PyYAML, and Typst) to regenerate the marked
  sections of `public/index.html` and the CVs in `public/files/`, then commit the result.
