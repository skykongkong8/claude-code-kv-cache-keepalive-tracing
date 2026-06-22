# pptx-res — deck-ready source for `mckinsey-pptx`

This folder repackages the `cache-keepalive` experiment (see `../findings.md`) into the input
format expected by **[seulee26/mckinsey-pptx](https://github.com/seulee26/mckinsey-pptx)**, which
reads source files from an `inputs/` folder and writes a `.pptx` to `output/`.

## Layout

```
pptx-res/
├── inputs/
│   ├── 00-storyboard.md            # slide-by-slide brief (template + data binding per slide)
│   ├── 01-key-numbers.md           # every figure to put on a slide, pre-formatted
│   ├── data/
│   │   ├── kpis.csv                 # per-arm CHR / CWT / ECM / token totals
│   │   ├── gap-boundary.csv         # DECISIVE: cache state on first turn after the gap
│   │   ├── ttl-write-breakdown.csv  # 5m vs 1h write share (0% / 100%)
│   │   ├── keepalive-turns.csv      # the cheap keepalive reads that fired
│   │   └── counterfactual-5min-ttl.csv  # what the plugin would save at a 5-min TTL
│   └── images/                      # pre-rendered charts (drop-in slide images)
│       ├── chart-gap-boundary.png   # the money shot
│       ├── chart-chr.png
│       ├── chart-totals.png
│       ├── chart-verdict.png
│       ├── chart-per-turn-rate.png
│       └── chart-cumulative-cwt.png
└── output/                          # generated .pptx lands here (.gitkeep placeholder)
```

## How to generate the deck (conversational — primary path)

From a session that has the `mckinsey-pptx` tool available, point it at this folder:

> "Build a McKinsey-style decision deck from the files in `pptx-res/inputs/`. Follow the
> slide-by-slide plan in `00-storyboard.md`, use the exact figures in `01-key-numbers.md`, bind the
> CSVs in `data/` to the chart slides, and place the PNGs in `images/` where the storyboard names
> them. Answer-first, one idea per slide, action titles. Save to `pptx-res/output/`."

The storyboard already names the McKinsey template for each slide (`dark_navy_summary`,
`executive_summary_takeaways`, clustered-bar, 2x2 matrix, waterfall, etc.), so the tool can map
content to templates directly.

## How to generate the deck (Python API — fallback)

```python
from mckinsey_pptx import PresentationBuilder

b = PresentationBuilder(default_section_marker="cache-keepalive A/B")
b.add("dark_navy_summary",
      body="On this 1-hour-TTL, subscription-billed install the plugin saves nothing and "
           "costs quota. Leave it off.")
b.add("executive_summary_takeaways", sections=[
    {"takeaway": "Cache TTL here is 1 hour, not 5 minutes",
     "bullets": ["100% of 466,136 write tokens used ephemeral_1h", "0 used ephemeral_5m"]},
    {"takeaway": "At a 7-min gap the cache stays warm without the plugin",
     "bullets": ["First post-gap turn was read-dominated in all four 7-min arms (35k-45k read)"]},
    {"takeaway": "Each keepalive ping is a wasted subscription request",
     "bullets": ["Subscription bills request count; defaults can fire up to 7 pings per pause"]},
])
# ...bind data/*.csv and images/*.png to the remaining slides per 00-storyboard.md...
b.save("output/cache-keepalive-verdict.pptx")
```

## Provenance

All numbers trace to `../results/{kpis,usage}.csv` and `../findings.md`; charts are copied verbatim
from `../results/*.png`. Nothing here is newly computed — this folder only re-shapes existing,
verified results into deck-input form.
