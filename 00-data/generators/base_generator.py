"""
Base Event Generator for Medallion Pipeline

Provides common functionality for all event generators:
- Writing JSON Lines files to Unity Catalog Volumes
- Configurable batch sizes and file naming
- Random seed support for reproducibility
- Historical backfill support for generating data across date ranges

Supports two modes:
1. Real-time mode: Events have current timestamp (default)
2. Historical backfill mode: Events distributed across a date range
"""

import json
import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class BaseEventGenerator(ABC):
    """
    Abstract base class for event generators.
    
    Subclasses must implement:
        - generate_event(): Create a single event record
        - source_name: Property returning the source identifier
    
    Supports two modes:
        - Real-time: Events generated with current timestamp
        - Historical backfill: Events distributed across a configurable date range
    """
    
    def __init__(
        self,
        volume_path: str,
        batch_size: int = 100,
        random_seed: Optional[int] = None,
        # Historical backfill parameters
        historical_days: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        """
        Initialize the generator.
        
        Args:
            volume_path: Path to Unity Catalog Volume (e.g., /Volumes/catalog/schema/volume/source)
            batch_size: Number of events to generate per batch (real-time) or per day (backfill)
            random_seed: Optional seed for reproducible generation
            historical_days: Number of days of historical data to generate (enables backfill mode)
            start_date: Explicit start date for backfill (alternative to historical_days)
            end_date: End date for backfill (defaults to today)
        """
        self.volume_path = volume_path
        self.batch_size = batch_size
        self._rng = random.Random(random_seed)
        self._random_seed = random_seed
        
        # Historical backfill configuration
        self._setup_date_range(historical_days, start_date, end_date)
        
        # Track current date during historical generation
        self._current_historical_date: Optional[datetime] = None
    
    def _setup_date_range(
        self,
        historical_days: Optional[int],
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> None:
        """Configure date range for historical backfill."""
        self.end_date = end_date or datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if historical_days:
            self.start_date = self.end_date - timedelta(days=historical_days)
            self._backfill_mode = True
        elif start_date:
            self.start_date = start_date
            self._backfill_mode = True
        else:
            self.start_date = None
            self._backfill_mode = False
        
        # Build list of dates for backfill
        self._date_range: List[datetime] = []
        if self._backfill_mode and self.start_date:
            current = self.start_date
            while current <= self.end_date:
                self._date_range.append(current)
                current += timedelta(days=1)
    
    @property
    def is_backfill_mode(self) -> bool:
        """Return True if generator is in historical backfill mode."""
        return self._backfill_mode
    
    @property
    def date_range(self) -> List[datetime]:
        """Return list of dates for historical backfill."""
        return self._date_range
        
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the source identifier (e.g., 'pos', 'ecommerce')."""
        pass
    
    @abstractmethod
    def generate_event(self) -> Dict[str, Any]:
        """Generate a single event record. Must be implemented by subclasses."""
        pass
    
    def generate_batch(self, num_events: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Generate a batch of events.
        
        Args:
            num_events: Number of events to generate (defaults to batch_size)
            
        Returns:
            List of event dictionaries
        """
        count = num_events or self.batch_size
        return [self.generate_event() for _ in range(count)]
    
    def write_batch(
        self,
        num_events: Optional[int] = None,
        file_prefix: Optional[str] = None
    ) -> str:
        """
        Generate events and write to Volume as JSON Lines file.
        
        Args:
            num_events: Number of events to generate (defaults to batch_size)
            file_prefix: Optional prefix for filename (defaults to source_name)
            
        Returns:
            Path to the created file
        """
        # Generate events
        events = self.generate_batch(num_events)
        
        # Create filename with timestamp
        now = datetime.now()
        prefix = file_prefix or self.source_name
        file_name = f"{prefix}_{now.strftime('%Y%m%d_%H%M%S')}.json"
        
        # Ensure output directory exists
        output_path = Path(self.volume_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Write as JSON Lines (one JSON object per line)
        file_path = output_path / file_name
        with open(file_path, 'w') as f:
            for event in events:
                f.write(json.dumps(event) + '\n')
        
        return str(file_path)
    
    def write_batch_dbutils(
        self,
        dbutils,
        num_events: Optional[int] = None,
        file_prefix: Optional[str] = None
    ) -> str:
        """
        Generate events and write to Volume using dbutils (for Databricks notebooks).
        
        This method is useful when running in Databricks where direct file writes
        may not work with Volume paths.
        
        Args:
            dbutils: Databricks dbutils object
            num_events: Number of events to generate
            file_prefix: Optional prefix for filename
            
        Returns:
            Path to the created file
        """
        # Generate events
        events = self.generate_batch(num_events)
        
        # Create filename with timestamp
        now = datetime.now()
        prefix = file_prefix or self.source_name
        file_name = f"{prefix}_{now.strftime('%Y%m%d_%H%M%S')}.json"
        
        # Create JSON Lines content
        content = '\n'.join(json.dumps(event) for event in events)
        
        # Write using dbutils
        file_path = f"{self.volume_path}/{file_name}"
        dbutils.fs.put(file_path, content, overwrite=True)
        
        return file_path
    
    # =========================================================================
    # Historical Backfill Methods
    # =========================================================================
    
    def generate_historical_batch(
        self,
        events_per_day: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate events across all dates in the historical range.
        
        Args:
            events_per_day: Number of events per day (defaults to batch_size)
            progress_callback: Optional callback(date, progress_pct) for progress tracking
            
        Returns:
            List of all generated events across all dates
        """
        if not self._backfill_mode:
            raise ValueError("Generator not in backfill mode. Initialize with historical_days parameter.")
        
        events_per_day = events_per_day or self.batch_size
        all_events = []
        total_days = len(self._date_range)
        
        for idx, date in enumerate(self._date_range):
            self._current_historical_date = date
            
            # Apply day-of-week variation (weekends get more traffic)
            daily_count = events_per_day
            if date.weekday() >= 5:  # Weekend
                daily_count = int(daily_count * 1.3)
            
            # Generate events for this day
            for _ in range(daily_count):
                event = self.generate_event()
                all_events.append(event)
            
            # Progress callback
            if progress_callback:
                progress_callback(date, (idx + 1) / total_days)
        
        self._current_historical_date = None
        return all_events
    
    def write_historical_batch(
        self,
        dbutils=None,
        events_per_day: Optional[int] = None,
        file_per_day: bool = True,
        progress_callback: Optional[callable] = None
    ) -> List[str]:
        """
        Generate historical data and write to Volume.
        
        Args:
            dbutils: Databricks dbutils object (use if running in Databricks)
            events_per_day: Number of events per day (defaults to batch_size)
            file_per_day: If True, creates one file per day; if False, one file for all
            progress_callback: Optional callback(date, progress_pct) for progress tracking
            
        Returns:
            List of created file paths
        """
        if not self._backfill_mode:
            raise ValueError("Generator not in backfill mode. Initialize with historical_days parameter.")
        
        events_per_day = events_per_day or self.batch_size
        created_files = []
        total_days = len(self._date_range)
        
        if file_per_day:
            # Create one file per day
            for idx, date in enumerate(self._date_range):
                self._current_historical_date = date
                
                # Apply day-of-week variation
                daily_count = events_per_day
                if date.weekday() >= 5:  # Weekend
                    daily_count = int(daily_count * 1.3)
                
                # Generate events for this day
                events = [self.generate_event() for _ in range(daily_count)]
                
                # Write file
                file_name = f"{self.source_name}_{date.strftime('%Y%m%d')}_backfill.json"
                file_path = self._write_events(events, file_name, dbutils)
                created_files.append(file_path)
                
                # Progress callback
                if progress_callback:
                    progress_callback(date, (idx + 1) / total_days)
            
            self._current_historical_date = None
        else:
            # Generate all events and write to single file
            all_events = self.generate_historical_batch(events_per_day, progress_callback)
            file_name = f"{self.source_name}_backfill_{self.start_date.strftime('%Y%m%d')}_{self.end_date.strftime('%Y%m%d')}.json"
            file_path = self._write_events(all_events, file_name, dbutils)
            created_files.append(file_path)
        
        return created_files
    
    def _write_events(self, events: List[Dict], file_name: str, dbutils=None) -> str:
        """Write events to file, using dbutils if provided."""
        content = '\n'.join(json.dumps(event) for event in events)
        file_path = f"{self.volume_path}/{file_name}"
        
        if dbutils:
            dbutils.fs.put(file_path, content, overwrite=True)
        else:
            output_path = Path(self.volume_path)
            output_path.mkdir(parents=True, exist_ok=True)
            with open(output_path / file_name, 'w') as f:
                f.write(content)
            file_path = str(output_path / file_name)
        
        return file_path
    
    def historical_timestamp(self, date: Optional[datetime] = None) -> str:
        """
        Generate a random timestamp for a specific date.
        
        Args:
            date: Date to generate timestamp for (defaults to current historical date)
            
        Returns:
            ISO format timestamp with random time during retail hours (8am-10pm)
        """
        target_date = date or self._current_historical_date or datetime.now()
        
        # Random hour between 8am and 10pm (retail hours)
        hour = self._rng.randint(8, 22)
        minute = self._rng.randint(0, 59)
        second = self._rng.randint(0, 59)
        microsecond = self._rng.randint(0, 999999)
        
        return target_date.replace(
            hour=hour, 
            minute=minute, 
            second=second,
            microsecond=microsecond
        ).isoformat()
    
    # =========================================================================
    # Helper methods for subclasses
    # =========================================================================
    
    def random_choice(self, choices: List[Any]) -> Any:
        """Select a random item from a list."""
        return self._rng.choice(choices)
    
    def random_int(self, min_val: int, max_val: int) -> int:
        """Generate a random integer in range [min_val, max_val]."""
        return self._rng.randint(min_val, max_val)
    
    def random_float(self, min_val: float, max_val: float, decimals: int = 2) -> float:
        """Generate a random float in range [min_val, max_val]."""
        return round(self._rng.uniform(min_val, max_val), decimals)
    
    def random_bool(self, probability: float = 0.5) -> bool:
        """Return True with given probability."""
        return self._rng.random() < probability
    
    def random_id(self, prefix: str, max_val: int, width: int = 5) -> str:
        """Generate a random ID string like 'PREFIX-00042'."""
        return f"{prefix}-{self._rng.randint(1, max_val):0{width}d}"
    
    def current_timestamp(self) -> str:
        """
        Return timestamp in ISO format.
        
        In backfill mode: Returns random timestamp for current historical date
        In real-time mode: Returns current timestamp
        """
        if self._backfill_mode and self._current_historical_date:
            return self.historical_timestamp(self._current_historical_date)
        return datetime.now().isoformat()
