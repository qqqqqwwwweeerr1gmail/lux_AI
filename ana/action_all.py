


r 14 11
m m_2 n
dc 14 9
dl 14 11 14 9

bcity u_2
bw 14 9
dx 14 4

dt 9 12 15 'H'





def circle(x: int, y: int) -> str:
    return f"dc {x} {y}"

def x(x: int, y: int) -> str:
    return f"dx {x} {y}"

def line(x1: int, y1: int, x2: int, y2: int) -> str:
    return f"dl {x1} {y1} {x2} {y2}"

# text at cell on map
def text(x: int, y: int, message: str, fontsize: int = 16) -> str:
    return f"dt {x} {y} {fontsize} '{message}'"

# text besides map
def sidetext(message: str) -> str:
    return f"dst '{message}'"















