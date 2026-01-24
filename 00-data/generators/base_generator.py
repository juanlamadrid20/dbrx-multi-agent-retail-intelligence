"""
Base Event Generator for Medallion Pipeline

Provides common functionality for all event generators:
- Writing JSON Lines files to Unity Catalog Volumes
- Configurable batch sizes and file naming
- Random seed support for reproducibility
"""

import json
import random
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class BaseEventGenerator(ABC):
    """
    Abstract base class for event generators.
    
    Subclasses must implement:
        - generate_event(): Create a single event record
        - source_name: Property returning the source identifier
    """
    
    def __init__(
        self,
        volume_path: str,
        batch_size: int = 100,
        random_seed: Optional[int] = None
    ):
        """
        Initialize the generator.
        
        Args:
            volume_path: Path to Unity Catalog Volume (e.g., /Volumes/catalog/schema/volume/source)
            batch_size: Number of events to generate per batch
            random_seed: Optional seed for reproducible generation
        """
        self.volume_path = volume_path
        self.batch_size = batch_size
        self._rng = random.Random(random_seed)
        
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
    
    # Helper methods for subclasses
    
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
        """Return current timestamp in ISO format."""
        return datetime.now().isoformat()
