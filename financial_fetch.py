from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class HistoricalDataRequest:
    ticker: str
    start: Optional[str] = None
    end: Optional[str] = None
    period: str = "1y"
    interval: str = "1d"


def fetch_historical_data(request: HistoricalDataRequest):
    import yfinance as yf

    ticker = request.ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker는 비어 있을 수 없습니다.")

    history_kwargs = {
        "interval": request.interval,
        "auto_adjust": True,
    }

    if request.start or request.end:
        history_kwargs["start"] = request.start
        history_kwargs["end"] = request.end
    else:
        history_kwargs["period"] = request.period

    data = yf.Ticker(ticker).history(**history_kwargs)
    if data.empty:
        raise RuntimeError(f"{ticker}의 과거 데이터를 찾지 못했습니다.")

    return data
