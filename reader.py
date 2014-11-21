#!/usr/bin/python

def read_from(fn = "regexps"):

  res = []
  with open(fn) as f:
    for line in f:
      res += process(line)

  return res


def process(line):
  line = line.strip()
  if line == "" or line.startswith("#"):
    return []

  return [line]

