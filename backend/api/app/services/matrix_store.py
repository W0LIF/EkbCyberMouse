from datetime import datetime

from api.app.models import HourlyFactor, TravelMatrix
from api.app.services.travel_time import adjusted_travel_seconds


class MatrixStore:
    def __init__(self):
        self._matrix_id = None
        self._points: list[str] = []
        self._durations: list[list[int]] = []
        self._distances: list[list[int]] = []
        self._hourly_factors: list[HourlyFactor] | None = None
        self._index: dict[str, int] = {}

    def store(self, matrix: TravelMatrix) -> None:
        self._matrix_id = matrix.matrix_id
        self._points = matrix.points
        self._durations = matrix.durations_sec
        self._distances = matrix.distances_m
        self._hourly_factors = matrix.hourly_factors
        self._index = {pid: i for i, pid in enumerate(self._points)}

    def is_loaded(self) -> bool:
        return self._matrix_id is not None

    def get(
        self,
        from_id: str,
        to_id: str,
        departure_time: datetime | None = None,
    ) -> tuple[int, int]:
        i, j = self._index.get(from_id), self._index.get(to_id)
        if i is None or j is None:
            return 0, 0
        duration = self._durations[i][j]
        if departure_time is not None:
            duration = adjusted_travel_seconds(
                duration,
                departure_time,
                self._hourly_factors or [],
            )
        return duration, self._distances[i][j]

    def as_matrix(self) -> TravelMatrix:
        """Собирает Pydantic-модель обратно для солвера."""
        if self._matrix_id is None:
            raise RuntimeError("Матрица времени в пути не загружена")
        return TravelMatrix(
            matrix_id=self._matrix_id,
            points=self._points,
            durations_sec=self._durations,
            distances_m=self._distances,
            hourly_factors=self._hourly_factors,
        )


matrix_store = MatrixStore()