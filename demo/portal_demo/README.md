# Portal Demo

This directory defines the reference layout for the portal demo package.
The package is prepared from a zebrafish deployment and distributed as a separate download.

## Scope

This demo package contains:
- one species: `zebrafish`
- Gene Info
- Bulk RNA
- scRNA
- scATAC
- BulkMulti
- JBrowse 2
- SequenceServer

## Download

- file: `portal_demo.tar.gz`
- url: `https://tulab.genetics.ac.cn/~qtu/miniodp/portal_demo.tar.gz`
- size: `1.7G`
- SHA256: `52dc9d37768a8baafbcb1bed3228913df7dba4ebfa9a4a9f5c9037553c60413b`

The checksum list is published at:

- `https://tulab.genetics.ac.cn/~qtu/miniodp/SHA256SUMS.txt`

## Layout

```text
demo/portal_demo/
├── dash/
│   └── data/
│       ├── species_adapters.toml
│       └── zebrafish/
│           ├── geneinfo.db
│           ├── geneinfo.toml
│           ├── bulkRNA/
│           ├── BulkMulti/
│           ├── scRNA/
│           └── scATAC/
├── hugo/
│   └── data/
│       └── species_display.toml
├── jbrowse2/
│   └── data/
│       └── Danio_rerio/
└── sequenceserver/
    └── data/
```

## Selected datasets

- scRNA:
  - `2023_DevCell_Farrell/003_004hpf`
- scATAC:
  - `2022_NatCommun_Crump/cranial_nc_005dpf`
- BulkMulti:
  - `2025Bulk`
- JBrowse 2:
  - `Danio_rerio`
- SequenceServer:
  - `Danio_rerio.GRCz11.cdna.all.fa*`

## Intended use

Use this subset to validate:
- species discovery in Dash
- gene search with `geneinfo.db`
- Bulk RNA loading from Parquet
- scRNA sample discovery and plotting
- scATAC sample discovery and plotting
- BulkMulti discovery and region-linked visualization
- JBrowse 2 loading for the zebrafish demo genome
- SequenceServer startup with a zebrafish cDNA database

## Integration notes

To test against the current repository:

1. Point Dash to `demo/portal_demo/dash/data/`, or copy the subset into a clean runtime data root.
2. Replace the Hugo species display config with `demo/portal_demo/hugo/data/species_display.toml` when building a single-species demo.
3. Copy `demo/portal_demo/jbrowse2/data/Danio_rerio/` into the JBrowse 2 app data directory before registering the assembly and tracks.
4. If you want to test the repository helper script directly against the demo bundle, run:

```bash
python jbrowse2/scripts/generate_loader.py Danio_rerio \
  --data-root demo/portal_demo/jbrowse2/data \
  --app-root demo/portal_demo/jbrowse2
```

This command is for repository-local validation. On a deployed JBrowse 2 host, keep using the real app and data roots.
5. Copy `demo/portal_demo/sequenceserver/data/` into `sequenceserver/data/` before starting SequenceServer.
