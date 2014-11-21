"""
Honeycomb grid.

This is a hexagonal(!) grid of sets of possible characters.

Additionally, we store information for each 'line'.

Coordinate systems are twofold:

For accessing lines, we give the basic direction (0, 1, 2) and the
anticlockwise count (0-based) from the corner in the range [0, 2(d-1)].

For accessing individual cells, we use an (a, b, c) coordinate system,
with the proviso that a+b+c = (d-1) * 3, where d, the basic dimension,
is the length of a single side of the hexagon.

d = 3.
                4
               / 3
              / / 2   a, dim=0
             / / / 1
      0 --- . . . / 0
 b,   1 -- . . . . /
 dim  2 - . . . . .
  =1  3 -- . . . . \
      4 --- . . . \ 4
             \ \ \ 3
              \ \ 2   c, dim=2
               \ 1
                0
"""

class Grid(object):
  def __init__(self, d, a, b, c, initial_cell = None):
    self.dim = d
    self.l = 2 * d - 1  # number of lines along a dimension
    self._coord_sum = 3 * (d - 1)  # sum of valid triple coordinates
    assert len(a) == self.l
    assert len(b) == self.l
    assert len(c) == self.l
    self.constraints = [a, b, c]
    if initial_cell is None:
      initial_cell = set()
    self.clear(initial_cell)
    self._marked = [ [ True ] * self.l for dim in 0, 1, 2 ]

    self._possibles = [ [ None ] * self.l for dim in 0, 1, 2 ]
    for dim in 0, 1, 2:
      for n in range(self.l):
        self.update_possibles(dim, n)

  def clear(self, initial):
    self._cells = {}
    for i in range(self.l):
      for j in range(self.l):
        c = self.coords(0, i, j)
        if c:
          self._cells[c] = initial

  def coords(self, dim, i, j):
    k = self._coord_sum - i - j
    if 0 <= k < self.l:
      c = [i, j, k]
      while dim > 0:
        dim -= 1
        c = c[-1:] + c[:-1]
      return tuple(c)
    return None

  def line(self, dim, i):
    l = []
    for j in range(self.l):
      c = self.coords(dim, i, j)
      if c:
        l.append(self._cells[c])
    return l

  def constraint(self, dim, i):
    return self.constraints[dim][i]

  def mark(self, dim, i, flag = True):
    #print "marking" if flag else "unmarking", dim, i
    self._marked[dim][i] = flag
    self.update_possibles(dim, i)

  def update_possibles(self, dim, i):
    m = 1
    for j in self.line(dim, i):
      m *= len(j)
    self._possibles[dim][i] = m

  def counts(self, dim, i):
    return self._possibles[dim][i]

  def marked(self, dim, i):
    return self._marked[dim][i]

  def line_update(self, dim, i, l):
    assert len(l) == self.l - abs(self.dim - 1 - i)
    j_start = max(0, self.dim - i - 1)
    for j in range(len(l)):
      c = self.coords(dim, i, j + j_start)
      if l[j] != self._cells[c]:
        #print "updating", c
        self._cells[c] = l[j]
        # Mark other lines than this one.
        for dim2 in 0, 1, 2:
          if dim2 != dim:
            self.mark(dim2, c[dim2])

    self.mark(dim, i, False)

  def __getitem__(self, (a, b, c)):
    if a + b + c != self._coord_sum:
      return None
    return self._cells[a, b, c]

  def __setitem__(self, (a, b, c), x):
    if a + b + c != self._coord_sum:
      raise KeyError
    if x == self._cells[a, b, c]:
      return
    self._cells[a, b, c] = x
    self.mark(0, a)
    self.mark(1, b)
    self.mark(2, c)

  def __str__(self):
    return self.stringify(format_cell)

  def stringify(self, format_cell):
    lines = []
    for b in range(self.l):
      line = " " * abs(self.dim - 1 - b)
      for cell in self.line(1, b):
        line += format_cell(cell) + " "
      lines.append(line)
    return "\n".join(lines)


def format_cell(c):
  if len(c) == 1:
    return list(c)[0]
  return "0.23456789+"[min(10, len(c))]

