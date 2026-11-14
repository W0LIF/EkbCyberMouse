from api.app.models import TravelMatrix

class MatrixStore:
    def __init__(self):
        self.matrix: TravelMatrix | None = None
        self.index_map: dict[str, int] = {}

    def store(self, matrix: TravelMatrix):
        self.matrix = matrix
        self.index_map = {point: i for i, point in enumerate(matrix.points)}

    def get(self, from_id: str, to_id: str) -> tuple[int, int]:
        if not self.matrix:
            raise ValueError("Матрица не загружена")
        i = self.index_map[from_id]
        j = self.index_map[to_id]
        return self.matrix.durations_sec[i][j], self.matrix.distances_m[i][j]

matrix_store = MatrixStore()