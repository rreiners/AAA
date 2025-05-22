"""
Chicago Taxi Data API Utilities
Efficient data collection from Chicago Data Portal using SODA API
"""

import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from pathlib import Path


class ChicagoTaxiAPI:
    """
    Chicago Taxi Data API client with advanced filtering and batch processing
    """

    def __init__(
        self, base_url="https://data.cityofchicago.org/resource/ajtu-isnz.json"
    ):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Chicago-Taxi-Analysis/1.0"})

    def get_metadata(self) -> Optional[Dict]:
        """Get dataset metadata"""
        metadata_url = "https://data.cityofchicago.org/api/views/ajtu-isnz.json"
        try:
            response = self.session.get(metadata_url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to fetch metadata: {e}")
            return None

    def build_query_params(
        self,
        limit: int = 1000,
        offset: int = 0,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        where_clause: Optional[str] = None,
        select_columns: Optional[List[str]] = None,
        order_by: str = "trip_start_timestamp DESC",
    ) -> Dict:
        """
        Build query parameters for the API call

        Args:
            limit: Number of records (max 50,000)
            offset: Starting record for pagination
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            where_clause: Custom SQL-like where clause
            select_columns: List of columns to select
            order_by: Sort order
        """
        params = {
            "$limit": min(limit, 50000),
            "$offset": offset,
            "$order": order_by,
        }

        # Build where clause
        where_conditions = []

        if start_date and end_date:
            where_conditions.append(
                f"trip_start_timestamp between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
            )
        elif start_date:
            where_conditions.append(
                f"trip_start_timestamp >= '{start_date}T00:00:00'"
            )
        elif end_date:
            where_conditions.append(
                f"trip_start_timestamp <= '{end_date}T23:59:59'"
            )

        if where_clause:
            where_conditions.append(where_clause)

        if where_conditions:
            params["$where"] = " AND ".join(where_conditions)

        if select_columns:
            params["$select"] = ",".join(select_columns)

        return params

    def fetch_data(self, **kwargs) -> Optional[pd.DataFrame]:
        """
        Fetch data with specified parameters
        """
        params = self.build_query_params(**kwargs)

        try:
            response = self.session.get(
                self.base_url, params=params, timeout=60
            )
            response.raise_for_status()

            data = response.json()
            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            return df

        except requests.exceptions.RequestException as e:
            print(f"❌ API request failed: {e}")
            return None
        except Exception as e:
            print(f"❌ Error processing response: {e}")
            return None

    def fetch_in_batches(
        self,
        total_records: int = 10000,
        batch_size: int = 50000,
        delay_seconds: float = 1.0,
        save_batches: bool = True,
        output_dir: Optional[Path] = None,
        **query_kwargs,
    ) -> Optional[pd.DataFrame]:
        """
        Fetch large dataset in batches
        """
        if output_dir is None:
            output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)

        all_batches = []
        records_fetched = 0
        batch_num = 1

        print(f"📦 Fetching {total_records} records in batches of {batch_size}")

        while records_fetched < total_records:
            remaining = total_records - records_fetched
            current_limit = min(batch_size, remaining)

            print(
                f"🔄 Batch {batch_num}: fetching {current_limit} records (offset: {records_fetched})"
            )

            batch_df = self.fetch_data(
                limit=current_limit, offset=records_fetched, **query_kwargs
            )

            if batch_df is None or len(batch_df) == 0:
                print(f"⚠️  No more data available at offset {records_fetched}")
                break

            all_batches.append(batch_df)
            records_fetched += len(batch_df)

            if save_batches:
                batch_file = output_dir / f"taxi_batch_{batch_num:03d}.parquet"
                batch_df.to_parquet(batch_file, index=False)
                print(f"💾 Saved batch to {batch_file}")

            progress = records_fetched / total_records * 100
            print(
                f"📊 Progress: {records_fetched:,}/{total_records:,} ({progress:.1f}%)"
            )

            batch_num += 1
            time.sleep(delay_seconds)  # Be respectful to the API

        if all_batches:
            print("🔗 Combining batches...")
            combined_df = pd.concat(all_batches, ignore_index=True)

            # Save combined dataset
            combined_file = output_dir / "taxi_data_combined.parquet"
            combined_df.to_parquet(combined_file, index=False)
            print(
                f"✅ Saved combined dataset: {len(combined_df):,} records to {combined_file}"
            )

            return combined_df

        return None

    def get_sample_for_month(
        self, year: int = 2024, month: int = 1, sample_size: int = 5000
    ) -> Optional[pd.DataFrame]:
        """Get a sample of data for a specific month"""
        start_date = f"{year}-{month:02d}-01"

        # Calculate end date
        if month == 12:
            end_date = f"{year}-12-31"
        else:
            next_month = datetime(year, month + 1, 1)
            end_date = (next_month - timedelta(days=1)).strftime("%Y-%m-%d")

        return self.fetch_data(
            limit=sample_size, start_date=start_date, end_date=end_date
        )

    def explore_data_distribution(self) -> Dict:
        """
        Explore the temporal and spatial distribution of the data
        """
        print("🔍 EXPLORING DATA DISTRIBUTION")
        print("=" * 40)

        # Get recent sample
        recent_sample = self.fetch_data(limit=1000)
        if recent_sample is None or len(recent_sample) == 0:
            return {}

        analysis = {}

        # Convert timestamp
        if "trip_start_timestamp" in recent_sample.columns:
            recent_sample["trip_start_timestamp"] = pd.to_datetime(
                recent_sample["trip_start_timestamp"]
            )

            # Temporal analysis
            analysis["temporal"] = {
                "earliest": recent_sample["trip_start_timestamp"].min(),
                "latest": recent_sample["trip_start_timestamp"].max(),
                "date_range_days": (
                    recent_sample["trip_start_timestamp"].max()
                    - recent_sample["trip_start_timestamp"].min()
                ).days,
            }

            print(
                f"📅 Date range: {analysis['temporal']['earliest']} to {analysis['temporal']['latest']}"
            )
            print(f"📅 Span: {analysis['temporal']['date_range_days']} days")

        # Column analysis
        analysis["columns"] = {
            "total_columns": len(recent_sample.columns),
            "numeric_columns": recent_sample.select_dtypes(
                include=["number"]
            ).columns.tolist(),
            "datetime_columns": recent_sample.select_dtypes(
                include=["datetime"]
            ).columns.tolist(),
            "object_columns": recent_sample.select_dtypes(
                include=["object"]
            ).columns.tolist(),
        }

        print(f"📊 Columns: {len(recent_sample.columns)} total")
        print(f"   Numeric: {len(analysis['columns']['numeric_columns'])}")
        print(f"   DateTime: {len(analysis['columns']['datetime_columns'])}")
        print(f"   Text: {len(analysis['columns']['object_columns'])}")

        # Missing data analysis
        missing_pct = (
            recent_sample.isnull().sum() / len(recent_sample) * 100
        ).round(1)
        analysis["missing_data"] = missing_pct[missing_pct > 0].to_dict()

        if analysis["missing_data"]:
            print("\n🔍 Columns with missing data:")
            for col, pct in analysis["missing_data"].items():
                print(f"   {col}: {pct}%")

        return analysis
