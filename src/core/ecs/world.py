
class World:
    def __init__(self):
        self._components: dict[str, SparseSet] = {}
        self._generations: list[int] = []
        self._free_ids: list[int] = []
        self._next_id: int = 0

    def create_entity(self):
        if len(self._free_ids) == 0: