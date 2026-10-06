# Agent Rules

## Data and implementation integrity

- Do not hard-code dataset contents, copied sample predictions, expected evaluation scores, or fabricated labels into production code or reports. Read real inputs from explicit CLI options, configuration, environment variables, or a documented data manifest.
- Synthetic values are allowed only in clearly named test fixtures. Mark their reports and output as synthetic; never present them as results from a public or real-world dataset.
- Do not claim a public dataset has been downloaded, parsed, or evaluated unless the implementation actually reads its source files and produces results from those records. Static dataset descriptions and schema checks are not dataset evaluations.
- If a requested file, dataset, Drive link, credentialed resource, or external dependency is inaccessible or missing, stop work that depends on it. Tell the user exactly what is inaccessible and what path/access is needed. Do not silently skip it or replace it with mock data.
- In the same response, give the user a concrete manual retrieval/access command appropriate to the source (for example, a `git clone`, official dataset download command, or local path to upload). Ask the user to provide the downloaded files or accessible path, then continue independent work that does not depend on them.
- Keep external dataset downloads outside version control by default; record source, revision, license, and expected directory in a manifest. Never redistribute footage or annotations beyond their license terms.
- Evaluation outputs must record input file IDs, annotation source, split, sample counts, metric definitions, and whether results are synthetic, public-data, or project-recorded. Fail clearly when inputs are missing or labels do not cover evaluated frames.
