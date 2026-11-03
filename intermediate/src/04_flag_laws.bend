import Base

type Cover is Data:
  Hidden{}
  Marked{}
  Open{}

def toggle(c: Cover) -> Cover:
  match c:
    case Hidden{}:
      Marked{}
    case Marked{}:
      Hidden{}
    case Open{}:
      Open{}

law toggle_twice:
  for c: Cover
  {toggle(toggle(c)) == c : Cover}

def toggle_twice(c):
  match c:
    case Hidden{}:
      {==}
    case Marked{}:
      {==}
    case Open{}:
      {==}

law opened_stays_open:
  {toggle(Open{}) == Open{} : Cover}

def opened_stays_open():
  {==}
