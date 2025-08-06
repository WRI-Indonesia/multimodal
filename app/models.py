from dataclasses import dataclass


@dataclass
class DistrictOverlap:
    district: str
    province: str
    pct_overlap: float
