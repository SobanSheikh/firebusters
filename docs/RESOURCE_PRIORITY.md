# FlameLens Resource Priority and Usage

This document ranks the available NASA resources by their value to the FlameLens hackathon product. The ranking reflects product importance, not the historical or scientific importance of a resource.

## Usage Types

- **Requirements:** Challenge scope, constraints, and judging alignment.
- **Structured:** Normalized PostgreSQL records, filtering, and comparison.
- **Analytics:** Polars/PyArrow calculations and deterministic charts.
- **Spatial:** Multidimensional arrays, heatmaps, and field comparisons.
- **RAG:** Explanations grounded in page-level citations.
- **Knowledge graph:** Relationships between programs, facilities, investigations, publications, and files.
- **Case study:** Historical motivation and lessons learned.
- **Impact card:** A concise downstream technology or public-benefit example.

## P0: Project Definition

| Rank | Resource | Usage | Action |
| ---: | --- | --- | --- |
| 1 | [Flame in Freefall challenge](https://www.spaceappschallenge.org/2026/challenges/flame-in-freefall/) | Requirements | Preserve requirements and judging criteria; do not treat as scientific evidence. |
| 2 | NASA challenge-description transcript | Requirements | Extract the problem statement, expected users, constraints, and deliverables. |
| 3 | [NASA PSI repository](https://psi.nasa.gov/physci/repo) | Discovery and provenance | Use as the authoritative source for investigation metadata, files, licenses, and DOI links. |

## P1: Core Product Data

| Rank | Resource | Usage | Action |
| ---: | --- | --- | --- |
| 4 | [PSI-159: ACME CFI-G](<../data/ nasa/PSI_159>) | Structured, RAG, future raw analysis | Make this the primary experiment explorer. Index its 179 normal-flame tests and final report. |
| 5 | Selected PSI-159 raw data | Computer vision and signal analysis | Download only tests `21174 C2`, `21174 C3` or `C4`, and `21291 C1`, with one camera stream and matching sensor/event files. |
| 6 | [PSI-117: processed cool-flame data](<../data/ nasa/PSI_117>) | Analytics and charts | Build stable/oscillating cool-flame, three-stage combustion, extinction, radiance, and experiment/model views. |
| 7 | [PSI-115: smoke simulation](<../data/ nasa/PSI_115>) | Spatial visualization | Parse the 960 x 240 gravity/no-gravity fields and build temperature, smoke, particle, velocity, and difference heatmaps. |
| 8 | [PSI-142: counterflow extinction](<../data/ nasa/PSI_142>) | Analytics | Visualize hot/cool extinction, ozone effects, temperature, and chemiluminescence profiles. |

## P2: Supporting Experiment Coverage

| Rank | Resource | Usage | Action |
| ---: | --- | --- | --- |
| 9 | [PSI-10: ACME Flame Design](<../data/ nasa/PSI_10>) | Structured and RAG | Index 207 normal and 120 inverse flame tests for comparison and discovery. |
| 10 | [PSI-98: SAFFIRE-I](<../data/ nasa/PSI_98>) | Structured and safety context | Index SIBAL material tests and camera manifests. Obtain actual imagery later if needed. |
| 11 | [PSI-39: FLEX](<../data/ nasa/PSI_39>) | RAG and summary extraction | Extract droplet-combustion and extinction summaries from PDFs. Defer the Igor Pro file. |
| 12 | [PSI-101: SAME](<../data/ nasa/PSI_101>) | Hardware RAG | Use selected diagrams and documentation to explain smoke-generation and detection hardware. |
| 13 | [PSI-62: BASS-related metadata](<../data/ nasa/PSI_62>) | Catalog and knowledge graph | Create an investigation record and link it to solid-fuel flame-spread topics. |
| 14 | [PSI-60: SPICE metadata](<../data/ nasa/PSI_60>) | Catalog and knowledge graph | Create an investigation record; defer deeper analysis until numerical data is available. |

## P3: Scientific Explanation and Organization

| Rank | Resource | Usage | Action |
| ---: | --- | --- | --- |
| 15 | [NASA Combustion Science Researcher's Guide](<../data/ nasa/np-2015-10-034-jsc_combustion_in_reduced_gravity-iss-mini-book-011116-508.pdf>) | Foundational RAG and taxonomy | Chunk by section and page. Use for established science, not current program status. |
| 16 | [NASA Glenn Combustion Science](https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/) | Knowledge graph and current context | Ingest program descriptions and current/archived status while excluding navigation and unrelated news. |
| 17 | [NASA Science Combustion](https://science.nasa.gov/biological-physical/focus-areas/combustion-science/) | Publication graph and RAG | Link research categories, investigators, publications, and PSI investigations. |
| 18 | [Fluids and Combustion Facility / CIR](https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/science-facilities-on-the-iss/fluids-combustion-facility/) | Facility RAG and knowledge graph | Explain where experiments ran, which diagnostics were available, and how investigations share hardware. |

## P4: Current and Future Research

| Rank | Resource | Usage | Action |
| ---: | --- | --- | --- |
| 19 | [SoFIE](https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/solid-fuel-ignition-and-extinction-sofie/) | Current research context | Link historical fire risks to modern ignition, flame-spread, growth, and extinction studies. |
| 20 | [FM2](https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/flammability-of-materials-on-the-moon-fm2/) | Lunar mission relevance | Use as the forward-looking application of reduced-gravity material-flammability research. |
| 21 | [FLARE](https://www.nasa.gov/glenn/glenn-expertise-space-exploration/physical-sciences-program/combustion-science/flammability-limits-at-reduced-g-experiment-flare/) | Material-screening context | Explain correlations and limitations between terrestrial and microgravity flammability tests. |

## P5: Mission Fire and Safety Case Studies

| Rank | Resource | Usage | Action |
| ---: | --- | --- | --- |
| 22 | [Fire aboard Space Station Mir](https://www.nasa.gov/history/25-years-ago-fire-aboard-space-station-mir/) | Primary in-orbit fire case study | Connect ignition, dense smoke, detection, suppression, blocked evacuation, and training to SAME, PSI-115, BASS, and SAFFIRE. |
| 23 | [Apollo 1 investigation](https://sma.nasa.gov/sma-disciplines/accllp/apollo-1#investigation) | Primary historical safety case | Connect high oxygen, combustible materials, rapid fire spread, toxic products, hatch design, and corrective actions to modern research. |
| 24 | [Apollo 13 investigation](https://sma.nasa.gov/sma-disciplines/accllp/apollo-13) | Secondary engineering-safety case | Use for oxygen-system, insulation, qualification, redundancy, and fault-chain lessons; do not present as combustion experiment data. |

## P6: Technology Impact

| Rank | Resource | Usage | Action |
| ---: | --- | --- | --- |
| 25 | [NASA Spinoff: Fire Detector](https://spinoff.nasa.gov/node/9407) | Detection impact card | Relate combustion-particle detection and false-alarm reduction thematically to SAME and PSI-115. Do not claim direct lineage without evidence. |
| 26 | [NASA Spinoff: Fire Attire](https://spinoff.nasa.gov/node/9918) | Materials impact card | Show how space-derived fire-resistant and thermal-protection materials benefited terrestrial firefighters. |
| 27 | [NASA Spinoff: Fireman's Air Tanks](https://spinoff.nasa.gov/node/9582) | Technology-transfer card | Include as a lightweight public-benefit example, not a core combustion resource. |

## Source Handling Rules

1. Keep the original NASA files immutable under `data/ nasa/`.
2. Store normalized tables and derived assets separately from originals.
3. Preserve investigation ID, original filename, sheet or row, units, DOI, URL, and transformation provenance.
4. Embed explanatory text and document chunks, not raw numerical rows.
5. Query structured data through SQL and analyze measurements deterministically.
6. Label historical articles, investigation reports, experiments, simulations, and publications as distinct evidence types.
7. Do not imply causal relationships between a PSI dataset and a NASA spinoff unless an authoritative source documents the relationship.
8. For current-status claims, prefer current NASA program pages over older guidebooks.

## MVP Implementation Order

1. Ingest PSI-159's experiment table and final report.
2. Normalize and visualize PSI-117 processed data.
3. Parse and visualize PSI-115 gravity/no-gravity fields.
4. Ingest the Researcher's Guide with page-level citations.
5. Add NASA Glenn and CIR program/facility relationships.
6. Add Mir and Apollo 1 safety-case cards.
7. Add the fire-detector impact card.
8. Download and integrate one controlled PSI-159 raw-data comparison.
9. Add PSI-10 and PSI-142 supporting analyses.
10. Add remaining resources as catalog entries and external links.

## MVP Boundary

The MVP is an evidence-backed combustion research workspace, not a general NASA archive. A user should be able to ask a question and receive matching experiments, computed comparisons, visualizations, and traceable NASA citations. Resources outside that workflow should remain lightweight catalog or impact entries.
