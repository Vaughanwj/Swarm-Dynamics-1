# Builds the paper: TeX Live (medium scheme) plus the few packages it lacks.
#   docker build -t swarm-village-paper paper
#   docker run --rm -v "$PWD/paper:/work" -w /work swarm-village-paper latexmk -pdf main.tex
FROM texlive/texlive:latest-medium
RUN tlmgr update --self && tlmgr install threeparttable multirow makecell doclicense xifthen ifmtarg imakeidx ccicons hyperxmp csquotes placeins
