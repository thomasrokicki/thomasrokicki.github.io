// CV generated from data.yaml; built by `make` from the repository root.
// Live preview: typst watch --input lang=fr cv/cv.typ /tmp/cv.pdf

#let data = yaml("data.yaml")
#let lang = sys.inputs.at("lang", default: "en")
#let accent = rgb("#fca072")      // website accent, used for rules
#let accent-text = rgb("#a85024") // darker shade of the accent, readable as text
#let muted = luma(90)

#let labels = (
  en: (
    positions: "Positions",
    education: "Education",
    publications: "Publications",
    awards: "Awards",
    present: "present",
    to-appear: "To appear",
    thesis: "Thesis:",
    supervisors: "Supervisors:",
    jury: "Jury:",
    president: "president",
    reviewers: "reviewers",
    examiners: "examiners",
    sep: "; ",
    pdf: "PDF",
    code: "Code",
    video: "Video",
    website: "Website",
    thesis-link: "Manuscript",
    github: "GitHub",
    scholar: "Google Scholar",
    linkedin: "LinkedIn",
    twitter: "Twitter",
  ),
  fr: (
    positions: "Postes",
    education: "Formation",
    publications: "Publications",
    awards: "Distinctions",
    present: "aujourd'hui",
    to-appear: "À paraître",
    thesis: "Thèse\u{a0}:",
    supervisors: "Direction\u{a0}:",
    jury: "Jury\u{a0}:",
    president: "président",
    reviewers: "rapporteurs",
    examiners: "examinateurs",
    sep: "\u{a0}; ",
    pdf: "PDF",
    code: "Code",
    video: "Vidéo",
    website: "Site web",
    thesis-link: "Manuscrit",
    github: "GitHub",
    scholar: "Google Scholar",
    linkedin: "LinkedIn",
    twitter: "Twitter",
  ),
).at(lang)

// Picks the current language of a {en, fr} field; TODOs are shown in red.
#let tr(value) = {
  let s = if type(value) == dictionary { value.at(lang) } else { str(value) }
  if s.contains("TODO") { text(fill: red, weight: "bold", s) } else { s }
}

// Local links in data.yaml are relative to the website root.
#let resolve(url) = if url.contains(":") { url } else { data.profile.website + "/" + url }

#let link-label(kind) = if kind == "thesis" { labels.thesis-link } else { labels.at(kind) }

#let span(entry, ongoing: false) = {
  if "end" in entry [#tr(entry.start) -- #tr(entry.end)]
  else if ongoing [#tr(entry.start) -- #labels.present]
  else { tr(entry.start) }
}

#let section(title) = block(sticky: true, above: 1.6em, below: 0.9em, grid(
  columns: (auto, 1fr),
  column-gutter: 0.7em,
  align: horizon,
  text(size: 12.5pt, fill: accent-text, tracking: 0.04em, smallcaps(title)),
  line(length: 100%, stroke: 0.7pt + accent),
))

#let entry(title, dates, subtitle, location, body: none) = block(breakable: false, below: 1.1em)[
  #grid(
    columns: (1fr, auto),
    row-gutter: 0.55em,
    column-gutter: 1em,
    align: (left, right),
    strong(title), dates,
    emph(subtitle), text(fill: muted, location),
  )
  #if body != none { block(above: 0.6em, body) }
]

#set document(title: data.profile.name + " – CV", author: data.profile.name)
#set page(paper: "a4", margin: (x: 2cm, y: 1.8cm))
#set text(font: "Libertinus Serif", size: 10.5pt, lang: lang)
#set par(leading: 0.6em)
#show link: set text(fill: accent-text)

// Header: the subtitle is the current position (the one without an end date).
#let current = data.positions.find(p => "end" not in p)
#align(center)[
  #text(size: 24pt, tracking: 0.03em, smallcaps(data.profile.name))
  #v(0.1em)
  #text(size: 12pt, fill: muted)[
    #if current != none [#tr(current.title), #tr(current.institution)] else { data.profile.title }
  ]
  #v(0.1em)
  #(
    (data.profile.location, link("mailto:" + data.profile.email, data.profile.email))
      + (link(data.profile.website, data.profile.website.split("://").last()),)
      + data.profile.links.filter(l => l.at("cv", default: false)).map(l => link(l.url, labels.at(l.kind)))
  ).join(h(0.5em) + text(fill: accent)[·] + h(0.5em))
]

#section(labels.positions)
#for p in data.positions {
  entry(
    tr(p.title),
    span(p, ongoing: true),
    if "team" in p [#tr(p.institution), #tr(p.team)] else { tr(p.institution) },
    tr(p.location),
  )
}

#section(labels.education)
#for e in data.education {
  let details = ()
  if "thesis" in e { details.push([#labels.thesis #emph(tr(e.thesis))]) }
  if "supervisors" in e { details.push([#labels.supervisors #e.supervisors.join(", ")]) }
  if "jury" in e {
    let roles = ("president", "reviewers", "examiners").filter(r => r in e.jury)
    details.push([#labels.jury #roles.map(r => [#e.jury.at(r).join(", ") (#labels.at(r))]).join(labels.sep)])
  }
  entry(
    tr(e.degree),
    span(e),
    if "team" in e [#tr(e.institution), #tr(e.team)] else { tr(e.institution) },
    tr(e.location),
    body: if details.len() > 0 { set text(size: 9.5pt); details.join(linebreak()) },
  )
}

#section(labels.publications)
#let pubs = data.publications
#grid(
  columns: (auto, 1fr),
  column-gutter: 0.8em,
  row-gutter: 1em,
  ..pubs.enumerate().map(((i, p)) => (
    text(fill: accent-text)[[#(pubs.len() - i)]],
    [
      #p.authors.map(a => if a == data.profile.name { strong(a) } else { a }).join(", "). \
      #text(weight: "semibold", p.title). \
      #emph(p.venue) (#p.venue_short #p.year).
      #if p.year > datetime.today().year() [#labels.to-appear.]
      #h(1fr)
      #box(text(size: 9.5pt, p.at("links", default: ()).map(l => link(resolve(l.url), link-label(l.kind))).join(" · ")))
      #if "award" in p [\ #text(fill: accent-text)[★ #tr(p.award.label)]]
    ],
  )).flatten(),
)

#let awarded = pubs.filter(p => "award" in p)
#if awarded.len() > 0 {
  section(labels.awards)
  for p in awarded {
    block(below: 0.8em, grid(
      columns: (1fr, auto),
      column-gutter: 1em,
      align: (left, right),
      [*#tr(p.award.label)*, #p.venue_short #p.year --- #emph(p.title)], str(p.year),
    ))
  }
}
