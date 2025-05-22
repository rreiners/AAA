# taxi.py
import pandas as pd
from sodapy import Socrata
from typing import List, Optional, Dict, Any
from pathlib import Path
from tqdm import tqdm

class ChicagoTaxiAPI:
    """
    A client for fetching data from the Chicago Taxi Socrata dataset using sodapy.
    Dataset: https://data.cityofchicago.org/resource/ajtu-isnz.json
    """
    DEFAULT_DOMAIN = "data.cityofchicago.org"
    DEFAULT_DATASET_ID = "ajtu-isnz"

    def __init__(self,
                 app_token: Optional[str] = None,
                 domain: str = DEFAULT_DOMAIN,
                 dataset_id: str = DEFAULT_DATASET_ID):
        """
        Initializes the ChicagoTaxiAPI client.

        Args:
            app_token: Your Socrata App Token (optional, but recommended for higher rate limits).
            domain: The Socrata domain.
            dataset_id: The Socrata dataset identifier.
        """
        self.domain = domain
        self.dataset_id = dataset_id
        self.client = Socrata(self.domain, app_token, timeout=60) # Increased timeout
        self._socrata_metadata: Optional[Dict] = None # Cache for Socrata metadata

    def _get_socrata_metadata(self, refresh: bool = False) -> Dict:
        """
        Fetches and caches the Socrata metadata for the dataset.
        This metadata includes column names, Socrata data types, etc.
        """
        if self._socrata_metadata is None or refresh:
            try:
                # print(f"Fetching Socrata metadata for dataset {self.dataset_id}...")
                self._socrata_metadata = self.client.get_metadata(self.dataset_id)
            except Exception as e:
                print(f"❌ Failed to fetch Socrata metadata: {e}")
                self._socrata_metadata = {} # Avoid refetching on every call if failed
        return self._socrata_metadata or {}

    def get_column_socrata_types(self) -> Dict[str, str]:
        """
        Returns a mapping of fieldName to Socrata dataTypeName.
        """
        metadata = self._get_socrata_metadata()
        type_map = {}
        if metadata and "columns" in metadata:
            for col_info in metadata["columns"]:
                if "fieldName" in col_info and "dataTypeName" in col_info:
                    type_map[col_info["fieldName"]] = col_info["dataTypeName"]
        return type_map

    def convert_df_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts DataFrame columns to appropriate types based on Socrata metadata.
        """
        if df.empty:
            return df

        socrata_type_map = self.get_column_socrata_types()
        if not socrata_type_map:
            print("⚠️ Could not retrieve Socrata type information. Skipping detailed type conversion.")
            return df

        for field_name, socrata_type in socrata_type_map.items():
            if field_name in df.columns:
                try:
                    current_col = df[field_name]
            
                    if current_col.isnull().all() and socrata_type not in \
                       {"text", "checkbox", "url", "photo", "document", "html", "email", "phone", "point", "location"}: 
                        if socrata_type in {"calendar_date", "fixed_timestamp", "floating_timestamp"}:
                             df[field_name] = pd.to_datetime(current_col, errors='coerce')
                        continue

                    if socrata_type in {"number", "money"}:
                        df[field_name] = pd.to_numeric(current_col, errors='coerce')
                    elif socrata_type in {"calendar_date", "fixed_timestamp", "floating_timestamp"}:
                        df[field_name] = pd.to_datetime(current_col, errors='coerce')
                    elif socrata_type == "checkbox": # Socrata boolean type
                        # Convert common string representations of boolean beforeastype
                        if current_col.dtype == 'object':
                            # sodapy might return 'true'/'false' strings or actual booleans
                            map_to_bool = {'true': True, 'false': False, True: True, False: False}
                            # Only map if values are in the map, otherwise keep as is for astype to handle Nones
                            df[field_name] = current_col.map(lambda x: map_to_bool.get(str(x).lower() if pd.notnull(x) else x, pd.NA) if pd.notnull(x) else pd.NA)
                        df[field_name] = current_col.astype("boolean") # Pandas nullable boolean
                    elif socrata_type in {"text", "url", "photo", "document", "html", "email", "phone"}:
                        df[field_name] = current_col.astype("string") # Pandas nullable string
                    # 'point', 'location' etc. are often fine as objects or require specific geo-parsing

                except Exception as e:
                    print(f"⚠️ Failed to convert column '{field_name}' (Socrata type: {socrata_type}): {e}")
        return df

    def fetch_data(self,
                   select: Optional[str] = None,
                   where: Optional[str] = None,
                   order: Optional[str] = None,
                   limit: Optional[int] = 1000, # Default limit for a single call
                   offset: Optional[int] = None,
                   q: Optional[str] = None, # For full-text search
                   convert_types: bool = True,
                   **sodaql_params: Any  # For other SODAQL $parameters like $group
                   ) -> Optional[pd.DataFrame]:
        """
        Fetches data from the Socrata dataset.

        Args:
            select: SOQL SELECT clause (e.g., "col1, col2").
            where: SOQL WHERE clause (e.g., "col1 > 10 AND col2 = 'text'").
            order: SOQL ORDER BY clause (e.g., "col1 DESC").
            limit: Maximum number of records to return.
            offset: Offset for records.
            q: Full-text search query.
            convert_types: Whether to attempt automatic type conversion based on Socrata metadata.
            **sodaql_params: Additional SODAQL parameters (e.g., group="column_name").

        Returns:
            A pandas DataFrame with the fetched data, or None if an error occurs.
        """
        query_params = {
            "select": select,
            "where": where,
            "order": order,
            "limit": limit,
            "offset": offset,
            "q": q,
            **{f"${key}": value for key, value in sodaql_params.items()} # Prepend $ to other params
        }
        # Remove None params so sodapy uses its defaults or omits them
        query_params = {k: v for k, v in query_params.items() if v is not None}

        try:
            # print(f"Fetching data with sodapy: {query_params}")
            results = self.client.get(self.dataset_id, **query_params)
            if results:
                df = pd.DataFrame.from_records(results)
                if convert_types and not df.empty:
                    df = self.convert_df_types(df)
                return df
            else:
                return pd.DataFrame() # Return empty DataFrame if no results
        except Exception as e:
            print(f"❌ Error fetching data with sodapy: {e}")
            return None

    def fetch_batch_data(self,
                       select: Optional[str] = None,
                       where: Optional[str] = None,
                       order: Optional[str] = None,
                       q: Optional[str] = None,
                       records_to_fetch: Optional[int] = None, # Max total records to fetch
                       batch_size: int = 50_000, # Socrata's typical max limit per request
                       convert_types: bool = True,
                       save_batches: bool = False,
                       output_dir: Optional[Path] = None,
                       **sodaql_params: Any
                       ) -> Optional[pd.DataFrame]:
        """
        Fetches all data matching the criteria, handling pagination.

        Args:
            select, where, order, q: SOQL clauses.
            records_to_fetch: If set, stops after fetching this many records. Otherwise, fetches all.
            batch_size: Number of records to fetch per API call (max usually 50000).
            convert_types: Whether to convert types for the final DataFrame.
            save_batches: If True, saves each fetched batch as a Parquet file.
            output_dir: Directory to save batches (if save_batches is True).
            **sodaql_params: Additional SODAQL parameters.

        Returns:
            A pandas DataFrame with all fetched data, or None.
        """
        if save_batches:
            if output_dir is None:
                output_dir = Path("data_batches_sodapy")
            output_dir.mkdir(parents=True, exist_ok=True)

        all_records_list = []
        current_offset = 0
        records_retrieved_so_far = 0
        
        # Determine total records for progress bar if records_to_fetch is not set
        # This requires an extra call to get a count, can be slow.
        # For simplicity, if records_to_fetch is None, tqdm might not show an accurate total
        # until the end, or we can try to get a count.
        # Let's try to get a count for a better progress bar experience.
        estimated_total = records_to_fetch
        if estimated_total is None:
            try:
                count_query_params = {"select": "COUNT(*)"}
                if where: count_query_params["where"] = where
                if q: count_query_params["q"] = q
                count_result = self.client.get(self.dataset_id, **count_query_params)
                if count_result and isinstance(count_result, list) and count_result[0]:
                    # The key for count can vary, often 'COUNT' or 'count_1', etc.
                    # Assuming the first key in the first dict is the count.
                    count_key = list(count_result[0].keys())[0]
                    estimated_total = int(count_result[0][count_key])
                    print(f"Estimated total records to fetch: {estimated_total}")
            except Exception as e:
                print(f"⚠️ Could not estimate total records for progress bar: {e}")
                # Fallback: progress bar will update without a fixed total initially if records_to_fetch is None
        
        pbar_total = records_to_fetch if records_to_fetch is not None else estimated_total
        with tqdm(total=pbar_total, desc="Fetching all data", unit="rec", disable=(pbar_total is None and records_to_fetch is None)) as pbar:
            while True:
                limit_for_this_batch = batch_size
                if records_to_fetch is not None:
                    remaining_to_fetch = records_to_fetch - records_retrieved_so_far
                    if remaining_to_fetch <= 0:
                        break
                    limit_for_this_batch = min(batch_size, remaining_to_fetch)

                batch_df = self.fetch_data(
                    select=select, where=where, order=order, q=q,
                    limit=limit_for_this_batch, offset=current_offset,
                    convert_types=False, # Convert types once at the end for the combined DF
                    **sodaql_params
                )

                if batch_df is None: # Error occurred
                    print(f"❗ Halting batch fetch due to an error in retrieving a batch at offset {current_offset}.")
                    break
                
                num_in_batch = len(batch_df)
                if num_in_batch == 0: # No more records
                    break

                all_records_list.append(batch_df)
                records_retrieved_so_far += num_in_batch
                current_offset += num_in_batch
                pbar.update(num_in_batch)

                if save_batches and output_dir:
                    batch_file = output_dir / f"batch_{len(all_records_list):04d}_offset_{current_offset-num_in_batch}.parquet"
                    batch_df.to_parquet(batch_file, index=False)

                if num_in_batch < limit_for_this_batch: # API returned fewer than requested, means end of data
                    break
                if records_to_fetch is not None and records_retrieved_so_far >= records_to_fetch:
                    break
            
            if pbar_total is None and records_to_fetch is None: # If we didn't have a total initially
                pbar.total = records_retrieved_so_far
                pbar.refresh()


        if not all_records_list:
            print("No data fetched.")
            return pd.DataFrame()

        print("🔗 Combining all fetched batches...")
        combined_df = pd.concat(all_records_list, ignore_index=True)

        if convert_types and not combined_df.empty:
            print("⚙️ Applying type conversions to combined data...")
            combined_df = self.convert_df_types(combined_df)

        print(f"✅ Total data fetched: {len(combined_df):,} records.")
        # save raw data
        raw_data_file = output_dir / "chicago_taxi_trips.parquet"
        combined_df.to_parquet(raw_data_file, index=False)

        return combined_df

    def close(self):
        """Closes the Socrata client session."""
        if self.client:
            self.client.close()