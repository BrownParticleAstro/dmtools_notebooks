Yes. Matplotlib does not ship one universal “scientific paper” style, but there are well-established, widely used solutions: ready-made style packages and standard rcParams configurations that produce publication-ready figures.
1. SciencePlots (most popular recommendation)
The SciencePlots package provides curated Matplotlib styles specifically for scientific papers, theses, and presentations.
Installation:
pip install SciencePlots
Basic usage:
import matplotlib.pyplot as plt
import scienceplots

plt.style.use('science')          # core scientific style
# or combine styles:
plt.style.use(['science', 'ieee'])   # IEEE-friendly (column width, B&W readable)
plt.style.use(['science', 'nature']) # Nature-style (sans-serif fonts)
plt.style.use(['science', 'grid'])   # with grid
It sets sensible defaults for:
	•	Figure size (≈ single-column width)
	•	Font family and sizes
	•	Line widths / tick styles
	•	Legend appearance
	•	High-quality export settings
	•	Optional LaTeX support
You can use it temporarily with a context manager:
with plt.style.context(['science', 'ieee']):
    # your plotting code
2. plotstyle package
Another option is the plotstyle package, which ships journal-specific presets (Nature, Science, IEEE, Elsevier, PLOS, ACS, etc.) with correct column widths, font sizes, and DPI.
import plotstyle
with plotstyle.use("nature") as style:
    fig, ax = style.figure(columns=1)
    # plot...
3. Manual `rcParams` configuration (no extra packages)
Many researchers define a reusable set of parameters. A solid starting point that works for most journals is:
import matplotlib.pyplot as plt

plt.rcParams.update({
    # Figure size & resolution
    "figure.figsize": (3.5, 2.5),      # single-column (~89 mm)
    "figure.dpi": 150,                 # screen
    "savefig.dpi": 300,                # or 600 for line art
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.05,

    # Fonts
    "font.family": "sans-serif",       # or "serif"
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 8,
    "axes.titlesize": 9,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,

    # Lines & axes
    "lines.linewidth": 1.0,
    "lines.markersize": 4,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": False,

    # Export (editable text in PDF/SVG)
    "pdf.fonttype": 42,   # TrueType
    "ps.fonttype": 42,
    "svg.fonttype": "none",
})
Typical journal column widths (inches):
Journal
Single column
Double column
Nature
3.5
7.2
Science
~3.4
~7.0
IEEE
3.5
7.16
Elsevier
3.54
7.48
PLOS
5.2
7.5
Extra tips for publication quality
	•	Prefer vector formats (PDF, EPS, SVG) over PNG when possible.
	•	Use colorblind-friendly palettes (e.g., Okabe–Ito, Paul Tol, or the cycles that come with SciencePlots).
	•	Design figures at final print size so fonts and line weights look correct.
	•	For LaTeX documents, the PGF backend or text.usetex=True can make text match the manuscript font exactly (requires a working TeX installation).
	•	Save a custom .mplstyle file and load it with plt.style.use("my_publication.mplstyle") for reuse across projects.
Bottom line: Start with SciencePlots (plt.style.use('science') or a journal-specific combination). It is the closest thing to a de-facto standard for scientific Matplotlib figures.
