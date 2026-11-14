from api.app.models import TravelMatrix


class MatrixStore:
    def __init__(self):
        self._matrix_id = None
        self._points: list[str] = []
        self._durations: list[list[int]] = []
        self._distances: list[list[int]] = []
        self._index: dict[str, int] = {}

    def store(self, matrix: TravelMatrix) -> None:
        self._matrix_id = matrix.matrix_id
        self._points = matrix.points
        self._durations = matrix.durations_sec
        self._distances = matrix.distances_m
        self._index = {pid: i for i, pid in enumerate(self._points)}

    def is_loaded(self) -> bool:
        return self._matrix_id is not None

    def get(self, from_id: str, to_id: str) -> tuple[int, int]:
        i, j = self._index.get(from_id), self._index.get(to_id)
        if i is None or j is None:
            return 0, 0
        return self._durations[i][j], self._distances[i][j]

    def as_matrix(self) -> TravelMatrix:
        """Собирает Pydantic-модель обратно для солвера."""
        return TravelMatrix(
            matrix_id=self._matrix_id,
            points=self._points,
            durations_sec=self._durations,
            distances_m=self._distances,
        )


matrix_store = MatrixStore()