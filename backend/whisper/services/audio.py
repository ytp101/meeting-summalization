from __future__ import annotations

import torch

__all__ = [
    "best_mono",
    "normalize_peak",
]


def best_mono(chunk: torch.Tensor) -> torch.Tensor:
    """
    Select the channel with the highest mean absolute amplitude as a proxy
    for the cleanest signal. Accepts (C, T) or (T,) and returns (T,).
    """
    if chunk.ndim == 1:
        return chunk.contiguous()
    if chunk.shape[0] == 1:
        return chunk.squeeze(0).contiguous()
    ch_energy = chunk.abs().mean(dim=1)  # (C,)
    best_idx = int(torch.argmax(ch_energy).item())
    return chunk[best_idx].contiguous()


def normalize_peak(x: torch.Tensor, peak_target: float = 0.95) -> torch.Tensor:
    """Peak-normalize a waveform tensor to a target amplitude."""
    peak = x.abs().max()
    if peak > 0:
        x = (x / peak) * peak_target
    return x.contiguous()

