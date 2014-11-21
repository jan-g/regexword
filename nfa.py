"""
An NFA library.
"""

from collections import defaultdict
import reg


class State(object):
  def __init__(self, label = None, counter = None, start = False, end = False):
    self.label = label
    if counter is not None:
      self.label = counter.counter()
      #print "Setting label to", self.label
    self.start = start
    self.end = end
    self._outs = defaultdict(set)
    self._ins = defaultdict(set)

  def add_epsilon(self, dest):
    self.add_out("", dest)

  def add_out(self, char, dest):
    self._outs[char].add(dest)
    dest.add_in(self, char)

  def out_labels(self):
    return self._outs.keys()

  def outs(self, c):
    return self._outs[c]

  def add_in(self, source, char):
    self._ins[char].add(source)

  def in_labels(self):
    return self._ins.keys()

  def ins(self, c):
    return self._ins[c]

  def del_epsilon(self, dest):
    self.del_out("", dest)

  def del_out(self, char, dest):
    self._outs[char].remove(dest)
    dest.del_in(self, char)

  def del_in(self, source, char):
    self._ins[char].remove(source)


def epsilon_closure(states):
  res = set()
  more = states
  while more:
    res.update(more)
    more = set()
    for s in res:
      for d in s.outs(""):
        if d not in res:
          more.add(d)
  return res

def epsilon_closure_reverse(states):
  res = set()
  more = states
  while more:
    res.update(more)
    more = set()
    for s in res:
      for d in s.ins(""):
        if d not in res:
          more.add(d)
  return res


class NFA(object):
  def __init__(self, re = None, start = None, end = None):
    self.start = start
    self.end = end
    self._counter = 0
    if re is not None:
      self.start, self.end = nfa(re, lambda: State(counter = self))
    self._states = None
    self.start.start = True
    self.end.end = True
    #self.simplify()  # It's buggy at the moment

  def counter(self):
    """
    Used to supply a stable label to the State generation
    """
    self._counter += 1
    return self._counter

  def states(self):
    """
    Accumulate all of the states in this NFA into one
    handy set.
    """
    if self._states is None:
      s = set()
      more = set([ self.start ])
      while more:
        s.update(more)
        more = set()
        for s1 in s:
          for c in s1.out_labels():
            for s2 in s1.outs(c):
              if s2 not in s:
                more.add(s2)
      self._states = s

    return self._states

  def __str__(self):
    chars = set()
    states = {}
    for state in self.states():
      states[state.label] = state
      chars.update(state.out_labels())
    chars = sorted(chars)

    line = 'State |'
    count = 0
    for c in chars:
      line += ' ' + (c if c else 'e') + ' '
      count = (count + 1) % 3
      if count == 0:
        line += '|'
    lines = [ line ]
    lines.append('-' * len(line))

    for n in sorted(states.keys()):
      state = states[n]
      line = ' %4d |' % n
      count = 0
      for c in chars:
        outs = sorted(map(lambda s: s.label, state.outs(c)))
        if outs:
          line += ' %1s ' % ','.join(map(str, outs))
        else:
          line += ' - '
        count = (count + 1) % 3
        if count == 0:
          line += '|'
      lines.append(line)

    return '\n'.join(lines)

  def simplify(self):
    change = None
    while change != self.states():
      change = self.states()

      #print "Simplifying: number of states before =", len(change)
      #print self
      #print

      for s1 in self.states():
        for s2 in list(s1.outs("")):
          if s2.end or s1 is s2:
            #print "Skipping e-transition to end"
            continue
          # Remove the transition s1->s2
          self._states = None
          s1.del_epsilon(s2)
          # Clone all s2->s3 transitions to s1->s3
          for char in s2.out_labels():
            for s3 in s2.outs(char):
              #print "  Cloning", s2.label, "-(", char, ")->", s3.label, "to", s1.label
              s1.add_out(char, s3)


def nfa(re, state):
  if isinstance(re, reg.REChar):
    start = state()
    end = state()
    start.add_out(re.char, end)
    return start, end

  elif isinstance(re, reg.REConc):
    fas = map(lambda r: nfa(r, state), re.res)
    for i in range(len(fas) - 1):
      fas[i][1].add_epsilon(fas[i+1][0])
    return fas[0][0], fas[-1][1]

  elif isinstance(re, reg.REAlt):
    start = state()
    end = state()
    fas = map(lambda r: nfa(r, state), re.res)
    for fa in fas:
      start.add_epsilon(fa[0])
      fa[1].add_epsilon(end)
    return start, end

  elif isinstance(re, reg.REStar):
    start, end = nfa(re.re, state)
    start.add_epsilon(end)
    end.add_epsilon(start)
    return start, end

  elif isinstance(re, reg.REOpt):
    start, end = nfa(re.re, state)
    start.add_epsilon(end)
    return start, end

  elif isinstance(re, reg.REGroup):
    return nfa(re.re, state)

  elif isinstance(re, reg.REAny):
    start = state()
    end = state()
    for c in reg._alphabet:
      start.add_out(c, end)
    return start, end

  elif isinstance(re, reg.REClass):
    start = state()
    end = state()
    for c in re.set:
      start.add_out(c, end)
    return start, end

  elif isinstance(re, reg.REPlus):
    start, end = nfa(re.re, state)
    end.add_epsilon(start)
    return start, end

  else:
    raise ValueError("Can't nfa-create " + str(re.__class__) + " for " + str(re))

