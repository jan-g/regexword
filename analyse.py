"""
Perform some basic analysis on the REs given.
"""

import re
import reg
import nfa

class Impossible(Exception):
  pass

def alphabet(res):
  """
  Return the alphabet used.
  We tot up all characters mentioned, and add
  a single arbitrary "other" of _
  to represent the class of everything else.
  """
  return set([ c for re in res for c in re if c.isupper() ]).union('_')

def pattern(s):
  if s.find("\\") >= 0:
    return NativePattern(s)
  return FAPattern(s)

class Pattern(object):
  """
  A constraint object. This holds onto the original RE,
  the compiled RE (if it was compilable), the corresponding
  state machine (again, as appopriate) and provides an
  implementation of wash, squeeze and exhaust.
  """

  def wash(self, poss):
    poss2 = None
    while poss2 != poss:
      poss2 = poss
      # Forward pass...
      #print "WASHING forward"
      #print "  before:", self._dump_poss(poss)
      poss, _ = self._wash(poss,
                        self._nfa.start,
                        lambda s: nfa.epsilon_closure(s),
                        lambda c, s: s.outs(c))
      #print "  after:", self._dump_poss(poss)
      # ...and reverse
      #print "WASHING reverse"
      poss.reverse()
      poss, _ = self._wash(poss,
                        self._nfa.end,
                        lambda s: nfa.epsilon_closure_reverse(s),
                        lambda c, s: s.ins(c))
      poss.reverse()
      #print "  after:", self._dump_poss(poss)
    return poss

  def _dump_poss(self, poss):
    return ''.join(map( lambda s: '[' + ''.join(sorted(s)) + ']', poss))

  def _wash(self, poss, begin, close, advance):
    #print "WASHING"
    states = close(set([ begin ]))
    poss2 = []
    for char_set in poss:
      #print "  Wash, char set =", ''.join(sorted(char_set))
      #print "  Current states =", ','.join(map(str, sorted(map(lambda s: s.label, states))))
      new_char_set = set()
      new_states = set()
      for char in char_set:
        for state in states:
          outs = close(advance(char, state))
          if outs:
            #print '    Viable transition on', char, ' to ', map(lambda s: s.label, outs)
            new_char_set.add(char)
            new_states.update(outs)
      if not new_states:
        raise Impossible("wash has run out of state possibilities", len(poss), len(poss2), states, poss, poss2)
      states = new_states
      if not new_char_set:
        raise Impossible("wash has run out of character possibilities")
      poss2.append(new_char_set)
    return poss2, states

  def squeeze(self, poss):
    change = True
    while change:
      #print "SQUEEZE LOOP"
      change = False
      for k in range(len(poss)):
        poss, c = self._squeeze(poss, k)
        change = change or c
    return poss

  def _squeeze(self, poss, k):
    #print "  squeezing", k
    _, precursors = self._wash(poss[:k],
                        self._nfa.start,
                        lambda s: nfa.epsilon_closure(s),
                        lambda c, s: s.outs(c))

    poss.reverse()
    _, postcursors = self._wash(poss[:len(poss) - k - 1],
                        self._nfa.end,
                        lambda s: nfa.epsilon_closure_reverse(s),
                        lambda c, s: s.ins(c))
    poss.reverse()

    # Locate possible transitions from s1 in precursors to s2 in postcursors.
    trans = set()
    change = False
    for char in poss[k]:
      for s1 in precursors:
        if s1.outs(char).intersection(postcursors):
          trans.add(char)
          break
      else:
        change = True  # as well as inevitable

    if not trans:
      raise Impossible("squeeze has run out of possibilities", poss, k, precursors, postcursors)
    poss[k] = trans
    return poss, change

  def exhaust(self, constraints):
    #print "Attempting to exhaust possibilities"
    possible = [ set() for i in constraints ]
    for p in possibilities(constraints):
      if self._matcher.match(p):
        _update(possible, p)
    return possible


def _update(constraints, string):
  assert len(constraints) == len(string)
  for i in range(len(string)):
    constraints[i].add(string[i])


def possibilities(constraints):
  if constraints == []:
    yield ""
  else:
    for p in constraints[0]:
      for ps in possibilities(constraints[1:]):
        yield p + ps


class NativePattern(Pattern):
  def __init__(self, s):
    self.string = s
    self._re = reg.parse(reg.approximate(s))
    self._nfa = nfa.NFA(self._re)
    self._matcher = re.compile("^" + s + "$")

  def __str__(self):
    return self.string


class FAPattern(Pattern):
  def __init__(self, s):
    self.string = s
    self._re = reg.parse(s)
    self._nfa = nfa.NFA(self._re)

    try:
      self._matcher = re.compile("^" + s + "$")
    except:
      print "Using our own implementation of the matcher"
      self._matcher = self  # We'll supply the match implementation

  def __str__(self):
    return str(self._re)

  def match(self, string):
    states = nfa.epsilon_closure(set([ self._nfa.start ]))
    for char in string:
      new = set()
      for s in states:
        new.update(nfa.epsilon_closure(s.outs(char)))
      states = new
      if not states:
        return False
    # Matched, are we at an accepting state?
    for s in states:
      if s.end:
        return True
    return False
