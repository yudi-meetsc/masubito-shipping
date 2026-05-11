from openpyxl.cell import Cell


def set_str(cell: Cell, value) -> None:
    """Write value as a forced-string cell (no auto type conversion)."""
    cell.value = str(value) if value is not None else ""
    cell.number_format = "@"
