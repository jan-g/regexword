"""
A regular expression representation.
"""

_alphabet = None

class RE(object):
  def bracket(self, other):
    #print "in bracket: self =", repr(self), " and other =", repr(other)
    return str(other) if other.prio <= self.prio else "{" + str(other) + "}"
    #return str(other) if other.__class__.prio <= self.__class__.prio else "{" + str(other) + "}"


class REChar(RE):
  prio = 0
  def __init__(self, c):
    self.char = c

  def __str__(self):
    return self.char


class REAny(RE):
  prio = 0
  def __init__(self, *args):
    pass

  def __str__(self):
    return "."


class REClass(RE):
  prio = 0
  def __init__(self, _set):
    #print "REClass, set =", _set
    self.set = set(_set)

  def __str__(self):
    return "[" + "".join(sorted(self.set)) + "]"


class RENotClass(REClass):
  prio = 0
  def __init__(self, _set, alphabet = None):
    #print "RENotClass, set =", _set
    if alphabet is None:
      alphabet = _alphabet

    self.aint = set(_set)
    super(RENotClass, self).__init__(alphabet.difference(self.aint))

  def __str__(self):
    return "[^" + "".join(sorted(self.aint)) + "]"


class REGroup(RE):
  prio = 0
  def __init__(self, re):
    self.re = re

  def __str__(self):
    return "(" + str(self.re) + ")"


class REStar(RE):
  prio = 5
  def __init__(self, re):
    #print "REStar: re =", repr(re)
    # R** = R*; R+* = R*; R?* = R*
    while isinstance(re, REStar) or isinstance(re, REPlus) or isinstance(re, REOpt):
      re = re.re
    self.re = re

  def __str__(self):
    return self.bracket(self.re) + "*"


class REOpt(RE):
  prio = 5
  def __init__(self, re):
    # R*? = R*; R?? = R?; R+? = R*
    # XXX: we only manage one of these here
    while isinstance(re, REOpt):
      re = re.re

    self.re = re

  def __str__(self):
    return self.bracket(self.re) + "?"

def re_opt(re):
  if isinstance(re, REStar):
    return re
  elif isinstance(re, REOpt):
    return re
  elif isinstance(re, REPlus):
    return REStar(re.re)
  return REOpt(re)


class REPlus(RE):
  prio = 5
  def __init__(self, re):
    # R*+ = R*; R?+ = R*; R++ = R+
    # XXX: we only manage one of these here
    while isinstance(re, REPlus):
      re = re.re

    self.re = re

  def __str__(self):
    return self.bracket(self.re) + "+"

def re_plus(re):
  #print "re_plus: re =", re
  if isinstance(re, REStar):
    return re
  elif isinstance(re, REOpt):
    return REStar(re.re)
  elif isinstance(re, REPlus):
    return re
  return REPlus(re)


class REConc(RE):
  prio = 7
  def __init__(self, *res):
    # {AB}C = ABC; A{BC} = ABC
    r = []
    for re in res:
      if isinstance(re, REConc):
        r += re.res
      else:
        r.append(re)
    self.res = r

  def __str__(self):
    return "".join( self.bracket(re) for re in self.res )


class REAlt(RE):
  prio = 10
  def __init__(self, *res):
    # {A|B}|C = A|B|C; A|{B|C} = A|B|C
    r = []
    for re in res:
      if isinstance(re, REAlt):
        r += re.res
      else:
        r.append(re)
    self.res = r

  def __str__(self):
    return "|".join( self.bracket(re) for re in self.res )


# Regular expression parsing.

class Tokeniser(object):
  START = '^'  # Initial value to prevent a concat
  CHAR = 'char'
  CLASS = 'class'
  NOT_CLASS = 'not_class'
  DOT = '.'
  CONCAT = '&'  # Generated tacitly
  LPAREN = '('
  RPAREN = ')'
  ALT = '|'
  STAR = '*'
  OPT = '?'
  PLUS = '+'
  EOS = '$'

  def __init__(self, s):
    self.remaining = s
    self.prev = self.START

  def __iter__(self):
    return self

  def next(self):
    if self.prev == self.CONCAT:
      self.prev = self.saved[0]
      return self.saved

    type, value = self.token()

    # Insert a tacit CONCAT between:
    # ab a( )a *a *( )( ?a ?( +a +(
    # where a and b stand for any primitive that consumes
    # a single character: char, dot, class, not_class

    if type in (self.CHAR, self.CLASS, self.NOT_CLASS, self.DOT) and \
       self.prev in (self.CHAR, self.CLASS, self.NOT_CLASS, self.DOT,
                     self.RPAREN, self.STAR, self.OPT, self.PLUS):
       self.saved = type, value
       self.prev = self.CONCAT
       return (self.CONCAT, None)

    elif type == self.LPAREN and \
         self.prev in (self.CHAR, self.CLASS, self.NOT_CLASS, self.DOT,
                       self.RPAREN, self.STAR, self.OPT, self.PLUS):
       self.saved = type, value
       self.prev = self.CONCAT
       return (self.CONCAT, None)

    elif type == self.EOS and self.prev == self.EOS:
       raise StopIteration

    else:
       self.prev = type
       return (type, value)

  def token(self):
    if self.remaining == "":
      return (self.EOS, None)

    if self.remaining.startswith("*"):
      self.remaining = self.remaining[1:]
      return (self.STAR, None)

    if self.remaining.startswith("?"):
      self.remaining = self.remaining[1:]
      return (self.OPT, None)

    if self.remaining.startswith("+"):
      self.remaining = self.remaining[1:]
      return (self.PLUS, None)

    if self.remaining.startswith("|"):
      self.remaining = self.remaining[1:]
      return (self.ALT, None)

    if self.remaining.startswith("("):
      self.remaining = self.remaining[1:]
      return (self.LPAREN, None)

    if self.remaining.startswith(")"):
      self.remaining = self.remaining[1:]
      return (self.RPAREN, None)

    if self.remaining.startswith("."):
      self.remaining = self.remaining[1:]
      return (self.DOT, None)

    if self.remaining[0] in _alphabet:
      c = self.remaining[0]
      self.remaining = self.remaining[1:]
      return (self.CHAR, c)

    if self.remaining.startswith("[^"):
      i = self.remaining.index("]")
      c = self.remaining[2:i]
      self.remaining = self.remaining[i+1:]
      return (self.NOT_CLASS, c)

    if self.remaining.startswith("["):
      i = self.remaining.index("]")
      c = self.remaining[1:i]
      self.remaining = self.remaining[i+1:]
      return (self.CLASS, c)

    raise ValueError("Unrecognised character in RE: %s" % self.remaining)


def ParseStart(item):
  #print "ParseStart called: stack top =", item
  return item
ParseStart.prio = 99

def ParseRParen(vals, ops):
  #print "ParseRParen called: stack top =", vals[-1]
  while ops[-1] != Tokeniser.LPAREN:
    #print "  ParseRParen working: stack top =", vals[-1], ops[-1]
    reduce(vals, ops)
  #print "  ParseRParen finishing"
  reduce(vals, ops)
  # We don't push a pesky RPAREN

def ParseEnd():
  #print "ParseEnd called"
  raise ValueError("ParseEnd called")
ParseEnd.prio = 99


def parse(s):
  #print "Parsing reg exp:", s
  vals = []  # Just basic RE subclasses
  ops = [ Tokeniser.START ]  # [ token ]

  for token, value in Tokeniser(s):
    if token in values:
      item = values[token](value)
      #print "  v =>", token, item
      vals.append(item)
      continue
    elif token in operators:
      constructor, n_params, push_prio, pop_prio = operators[token]
      # Lower precedence binds tighter
      while ops and push_prio >= operators[ops[-1]][3]:
        # Pop the operator and process it.
        #print "  o <=", ops[-1], "  forced by", token
        reduce(vals, ops)

      #print "  o =>", token
      ops.append(token)
    elif token in specials:
      specials[token](vals, ops)
    else:
      raise ValueError("Don't understand token: %s, %r" % (token, value))

  assert ops == [ Tokeniser.EOS ]
  assert len(vals) == 1
  return vals.pop()

values = {
      Tokeniser.CHAR: REChar,
      Tokeniser.DOT: REAny,
      Tokeniser.CLASS: REClass,
      Tokeniser.NOT_CLASS: RENotClass,
    }

operators = {
      # token : (fun, n_args, push_prio, pop_prio)
      Tokeniser.START: (ParseStart, 1, 99, 99),
      Tokeniser.EOS: (ParseEnd, 1, 99, 99),
      Tokeniser.STAR: (REStar, 1, 5, 5),
      Tokeniser.OPT: (re_opt, 1, 5, 5),
      Tokeniser.PLUS: (re_plus, 1, 5, 5),
      Tokeniser.CONCAT: (REConc, 2, 7, 7),
      Tokeniser.ALT: (REAlt, 2, 10, 10),
      Tokeniser.LPAREN: (REGroup, 1, 0, 12),
    }

specials = {
      Tokeniser.RPAREN: ParseRParen,
    }

def reduce(vals, ops):
  fun, n_args, _, _ = operators[ops.pop()]
  args = vals[-n_args:]
  del vals[-n_args:]
  #print "  v <=", args
  vals.append(fun(*args))
  #print "  v =>", repr(vals[-1]), vals[-1]


def approximate(s):
  """
  Given a non-regular expression (ie, one containing back-references),
  it is a theorem that everything it matches will be matched by an RE
  that replaces each back-reference by a copy of the sub-RE that it
  corresponds to. Such an RE will typically (ie, except in degenerate
  cases) accept a larger language than the original expression; however,
  we may nevertheless be able to use it to make progress with constraint
  satisfaction problems.
  This function turns such an expression into its near-equivalent RE.
  """
  starts = []
  ends = []
  depth = []
  res = ""
  i = 0
  while i < len(s):
    c = s[i]
    i += 1
    if c == "\\":
      n = int(s[i]) - 1
      i += 1
      res += "(" + res[starts[n]:ends[n]] + ")"
    else:
      res += c
      if c == "(":
        depth.append(len(starts))
        starts.append(len(res))  # Offset of first character of pattern
        ends.append(Ellipsis)  # Offset of corresponding end. We'll fill this in when found.
      elif c == ")":
        ends[depth.pop()] = len(res) - 1  # For indexing.

  return res

