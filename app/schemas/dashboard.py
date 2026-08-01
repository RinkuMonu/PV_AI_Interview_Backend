from pydantic import BaseModel
from typing import Optional

class DashboardMetric(BaseModel):
    title: str
    value: str
    trend: str
    percentage_change: float
    color: str
    icon: str
