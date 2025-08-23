from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PageSpec:
    name: str
    purpose: str
    components: List[str] = field(default_factory=list)


@dataclass
class AppSpec:
    name: str
    description: str
    pages: List[PageSpec]
    python_packages: List[str] = field(default_factory=list)
    extra_files: Dict[str, str] = field(default_factory=dict)

    @property
    def slug(self) -> str:
        import re

        s = re.sub(r"[^a-z0-9\\-]+", "-", self.name.lower())
        return s.strip("-") or "streamlit-app"
