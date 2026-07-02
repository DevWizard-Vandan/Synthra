"""Thread-safe priority campaign queue with timestamp FIFO override."""

import heapq
import time
from threading import Lock
from typing import Dict, List, Optional, Tuple

from synthra.core.domain import Campaign


class CampaignQueue:
    """Thread-safe priority campaign queue."""

    def __init__(self) -> None:
        """Initialize queue structure with lock and heap storage."""
        self._lock = Lock()
        # Elements are: (-priority, enqueue_timestamp, campaign_id)
        self._heap: List[Tuple[int, float, str]] = []
        self._campaigns: Dict[str, Tuple[Campaign, int]] = {}

    def enqueue(self, campaign: Campaign, priority: int = 0) -> None:
        """Add a campaign to the priority queue."""
        with self._lock:
            if campaign.id in self._campaigns:
                # Update priority if already present
                self._campaigns[campaign.id] = (campaign, priority)
                return

            entry = (-priority, time.time(), campaign.id)
            heapq.heappush(self._heap, entry)
            self._campaigns[campaign.id] = (campaign, priority)

    def dequeue(self) -> Optional[Tuple[Campaign, int]]:
        """Remove and return the highest priority campaign."""
        with self._lock:
            while self._heap:
                neg_priority, _, campaign_id = heapq.heappop(self._heap)
                if campaign_id in self._campaigns:
                    campaign, priority = self._campaigns.pop(campaign_id)
                    return campaign, priority
            return None

    def remove(self, campaign_id: str) -> None:
        """Remove a campaign from the queue."""
        with self._lock:
            self._campaigns.pop(campaign_id, None)

    def size(self) -> int:
        """Get the number of campaigns in the queue."""
        with self._lock:
            return len(self._campaigns)

    def get_all(self) -> List[Campaign]:
        """Return all enqueued campaigns."""
        with self._lock:
            return [campaign for campaign, _ in self._campaigns.values()]
