from api.app.models import TravelMatrix

class MatrixStore:
    def __init__(self):
        self._matrix_id = None
        self._points = []
        self._durations = []
        self._distances = []
        self._index = {}

    def store(self, matrix: TravelMatrix) -> None:
        self._matrix_id = matrix.matrix_id
        self._points = matrix.points
        self._durations = matrix.durations_sec
        self._distances = matrix.distances_m
        self._index = {pid: i for i, pid in enumerate(self._points)}

    def get(self, from_id: str, to_id: str) -> tuple[int, int]:
        if from_id not in self._index or to_id not in self._index:
            return 0, 0
        i = self._index[from_id]
        j = self._index[to_id]
        return self._durations[i][j], self._distances[i][j]

    def is_loaded(self) -> bool:
        return self._matrix_id is not None

matrix_store = MatrixStore()