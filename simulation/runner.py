from typing import Dict, Tuple
from .registry import get


def run_sim(sim_name: str, inputs: Dict) -> Tuple[Dict, Dict]:
    """
    returns: (observations: dict[str,float], meta: dict[str,any])
    meta may include cost_estimate_usd, seconds, backend.
    """
    fn = get(sim_name)
    return fn(inputs)
