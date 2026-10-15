"""mcd_pet —— 一只靠麦当劳养活的电子猫。"""

from .pet import Pet, status_card, death_card, stats_block, recommend
from . import foods, faces

__all__ = ["Pet", "foods", "faces", "status_card", "death_card", "stats_block", "recommend"]
__version__ = "1.0.0"
