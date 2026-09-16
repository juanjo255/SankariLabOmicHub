"""
Datasets API - Provides access to the curated per-species dataset manifest
(Run / Year / Data Type / Condition / Replicates / Description) that backs
the "Data Sources" tab.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

MANIFEST_COLUMNS = ["run", "year", "data_type", "condition", "replicates", "description"]

COLUMN_HEADERS = {
    "run": "Run",
    "year": "Year",
    "data_type": "Data Type",
    "condition": "Condition",
    "replicates": "Replicates",
    "description": "Description",
}


class DatasetsAPI:
    def __init__(self, species_key: str):
        if not species_key:
            raise ValueError("Species key is required and cannot be empty")
        if not isinstance(species_key, str):
            raise TypeError("Species key must be a string")

        self.species = species_key.strip()
        if not self.species:
            raise ValueError("Species key cannot be empty or whitespace")

        # Use global DASH_DATA_PATH or fall back to legacy path
        data_root = os.environ.get('DASH_DATA_PATH', Path(__file__).parent.parent / "data")
        self.data_dir = Path(data_root) / self.species
        self.manifest_file = self.data_dir / "Datasets" / "datasets_manifest.csv"

        self.logger = logger
        self._manifest = self._load_manifest()

    def _load_manifest(self) -> pd.DataFrame:
        """Load the manifest, falling back to an empty frame on any problem
        rather than raising, since this feature is optional per species."""
        if not self.manifest_file.exists():
            self.logger.warning(f"Datasets manifest not found: {self.manifest_file}")
            return pd.DataFrame(columns=MANIFEST_COLUMNS)

        try:
            df = pd.read_csv(self.manifest_file)
            missing = [c for c in MANIFEST_COLUMNS if c not in df.columns]
            if missing:
                self.logger.error(
                    f"Datasets manifest missing columns {missing}: {self.manifest_file}"
                )
                return pd.DataFrame(columns=MANIFEST_COLUMNS)
            self.logger.info("✅ Loaded %d dataset rows from %s", len(df), self.manifest_file)
            return df[MANIFEST_COLUMNS]
        except Exception as exc:
            self.logger.error(f"Error loading datasets manifest {self.manifest_file}: {exc}")
            return pd.DataFrame(columns=MANIFEST_COLUMNS)

    def is_available(self) -> bool:
        return not self._manifest.empty

    def get_dataframe(self) -> pd.DataFrame:
        """Return a copy of the datasets manifest."""
        return self._manifest.copy()

    def get_records(self) -> List[Dict]:
        """Return manifest rows as a list of dicts for dash_table.DataTable's `data` prop."""
        return self._manifest.to_dict("records")

    def get_columns(self) -> List[Dict[str, str]]:
        """Return dash_table column definitions with human-readable headers."""
        return [{"name": COLUMN_HEADERS.get(col, col), "id": col} for col in MANIFEST_COLUMNS]
