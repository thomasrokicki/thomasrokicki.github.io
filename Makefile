# Regenerate the website sections and both CVs from cv/data.yaml.
TYPST ?= typst
CV_EN := public/files/cv_thomas_rokicki.pdf
CV_FR := public/files/cv_thomas_rokicki_fr.pdf

.PHONY: all site
all: site $(CV_EN) $(CV_FR)

# Validates cv/data.yaml (stopping on errors) and rewrites the marked regions of public/index.html.
site:
	python3 cv/build.py

$(CV_EN): cv/cv.typ cv/data.yaml | site
	$(TYPST) compile --input lang=en $< $@

$(CV_FR): cv/cv.typ cv/data.yaml | site
	$(TYPST) compile --input lang=fr $< $@
