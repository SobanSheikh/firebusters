# PSI-115 numerical adapter

## Run locally

From `backend/`:

```bash
python3 -m app.psi115 --input '../data/ nasa/PSI_115' --output '../data/processed/psi115-v1'
python3 -m unittest discover -s tests -p test_psi115.py -v
```

Use a new output directory for each run. Originals remain untouched. No credentials or remote service are needed.

## Verified report context

`NNX17AF08A_FinalReport.pdf`, sections 4.1–4.3 (printed page 9), describes simulated DBP aerosol formation in a chamber, a nonuniform 960 by 240 mesh, reference temperature 300 K, heated-source temperature 473.2 K, and inlet velocities 0.08 and 0.10 m/s. Earth-gravity and zero-gravity cases are described, alongside cases changing settling, thermophoresis, and source orientation. Results in the report are presented at seven seconds. Section 3.1 formulates the fluid equations in dimensionless form.

These statements establish study context, not a complete export-format specification. The downloaded fields lack explicit physical coordinates, ordering instructions, and unit metadata. Do not automatically convert their values to kelvin, attach a physical mesh, or infer a time sequence from the report alone.

## Implemented formats

- Scalar grids: four positive integer header entries, last two equal to one, followed by exactly the declared number of finite values. Supports Fortran D exponents. Original value order is preserved.
- PSD files: explicit node-ID/value pairs, including the first line as data. Duplicate node IDs are rejected; original line numbers are retained.
- `nodeDiameters.dat`: recognized text header followed by strictly increasing positive diameters. No guessed node-ID join or unit conversion.

The local collection contains 42 DAT files. Seven grid files have more values than their declared shape. The adapter rejects these instead of truncating values: the four `10cmNoGravity` fields and `8cmNoGravityNumDenR.dat`, `8cmNoGravityuR.dat`, `8cmNoGravityvR.dat`.

## Output and provenance

`fields.json` describes parsing status, source checksum/ID, dataset-file citation, numerical extrema, and a bounded index-envelope preview. Valid files produce compressed JSON artifacts preserving all numerical values or node records; each artifact has a checksum. `report.json` summarizes successes, failures, and remaining limitations.

Source IDs match the general ingestion inventory. Dataset citations resolve to immutable original files. Previews use numerical array index, not distance; min/max envelopes preserve extremes without claiming spatial geometry. Every output remains `publishable: false` until scientific mapping is reviewed.

## Before production charts

1. Establish export ordering and physical coordinates from authoritative documentation or producer-provided data. A nonuniform mesh cannot be reconstructed by drawing evenly spaced physical coordinates.
2. Verify normalization and unit conversions separately for each quantity.
3. Diagnose extra samples in the seven rejected fields; document any approved repair as a versioned transformation.
4. Establish the mapping between PSD node IDs and diameter entries before plotting physical particle diameters.
5. Validate corresponding cases and compare rendered fields with report figures before enabling difference heatmaps.

This adapter is numerical ingestion and validation, not a trained model or an RAG embedding pipeline.
