class Domino:
    def __init__(self, id, a, b):
        self.id = id       
        self.values = (a, b)

    def __repr__(self):
        return f"Domino(id={self.id}, values={self.values})"


class Region:
    def __init__(self, indices, rtype, target=None):
        self.cells = [tuple(c) for c in indices]
        self.type = rtype
        self.target = target

    def __repr__(self):
        return f"Region(type={self.type}, target={self.target}, cells={self.cells})"


class Board:
    def __init__(self, dominoes, regions):
        self.dominoes = dominoes           
        self.regions = regions              

        self.region_map = self._build_region_map()
        self.rows, self.cols = self._compute_size()

    def _build_region_map(self):
        """map each cell (r,c) to region object."""
        mapping = {}
        for region in self.regions:
            for cell in region.cells:
                mapping[cell] = region
        return mapping

    def _compute_size(self):
        """compute board size based on highest cell index."""
        max_r = max(r for region in self.regions for (r, _) in region.cells)
        max_c = max(c for region in self.regions for (_, c) in region.cells)
        return max_r + 1, max_c + 1

    def __repr__(self):
        return (
            f"Board(size={self.rows}x{self.cols}, "
            f"dominoes={len(self.dominoes)}, regions={len(self.regions)})"
        )