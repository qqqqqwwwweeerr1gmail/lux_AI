# Example Cell and Position classes
class Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Cell:
    def __init__(self, pos):
        self.pos = pos

# Example list of Cell objects
cells = [
    Cell(Position(2, 3)),
    Cell(Position(1, 5)),
    Cell(Position(2, 1)),
    Cell(Position(1, 2)),
    Cell(Position(3, 4))
]

# Sort the list of Cell objects by x, then by y


team = 1
get_di = 'ew' # 'ns'


if team % 2 == 1:
    if get_di == 'ew':
        sorted_cells = sorted(cells, key=lambda cell: (-cell.pos.x, cell.pos.y))
    if get_di == 'ns':
        sorted_cells = sorted(cells, key=lambda cell: (cell.pos.x, -cell.pos.y))
else:
    sorted_cells = sorted(cells, key=lambda cell: (cell.pos.x, cell.pos.y))

# Print the sorted list
for cell in sorted_cells:
    print(f"Cell at x: {cell.pos.x}, y: {cell.pos.y}")























