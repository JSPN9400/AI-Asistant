from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ActionResult:
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

