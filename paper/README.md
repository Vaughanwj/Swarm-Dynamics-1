# Paper

*Red Tape at the End of the World: Self-Made Procedure, Votes for Comfort and Waiting to Be Asked in
Villages of LLM Agents, with a Pre-registered Probe.*

Preprint: https://doi.org/10.5281/zenodo.23535973. The software it reports is archived at
https://doi.org/10.5281/zenodo.23535975.

`main.tex` and `refs.bib` are the source, and `main.pdf` is the built paper. Build it with Docker
from the repository root:

```bash
docker build -t swarm-village-paper paper
```

```bash
docker run --rm -v "$PWD/paper:/work" -w /work swarm-village-paper latexmk -pdf main.tex
```

The paper is licensed CC BY 4.0.
