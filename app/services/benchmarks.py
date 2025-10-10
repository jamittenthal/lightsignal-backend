from ..schemas import Benchmark
from typing import List

def vector_benchmarks(naics: str, size: str, region: str, metrics: List[str]) -> List[Benchmark]:
    # Stub values; replace with Pinecone neighbors / peer stats
    demo = {"margin": (32.0, 0.6), "runway": (6.0, 0.55), "dso": (38.0, 0.62)}
    out = []
    for m in metrics:
        v, p = demo.get(m, (0.0, 0.5))
        out.append(Benchmark(metric=m, value=v, peer_percentile=p))
    return out
