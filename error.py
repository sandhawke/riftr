#!/usr/bin/env python
#      -*-mode: python -*-    -*- coding: utf-8 -*-
"""


"""

class Error (RuntimeError):
    pass

class InputError (Error):
    pass
    
class SyntaxError (InputError):

   def __init__(self, line, pos, input_text=None, message=None):
      self.line = line
      self.pos = pos
      self.input_text = input_text
      if message is None:
          self.message = ("syntax error, line %d, col %d, %s" % 
                          (line, self.col, self.msg))
      else:
          self.message = message

   msg = ""

   @property
   def col(self):
       if self.input_text:
           return find_column(self.input_text, self.pos)
       else:
           return 0

   def illustrate_position(self, prefix="==> "):
       return illustrate_position(self.input_text, 
                                  self.line,
                                  self.col,
                                  prefix)

class ParserError (SyntaxError):

    msg = "unexpected token"

class LexerError (SyntaxError):

    msg = "unexpected character"



# from PLY docs
def find_column(input_text,pos):
    i = pos
    while i > 0:
        if input_text[i] == '\n': break
        i -= 1
    column = (pos - i)+1
    return column

def illustrate_position(input_text, line, col, prefix="==> "):
    s = prefix + input_text.split("\n")[line-1] + "\n"
    s+= prefix + (" "*(col-1))+"^---- around here"
    return s

#   except lex.LexError, e:
#      pos = len(s) - len(e.text)
#      col = find_column(s, pos)
#      line = lex.lexer.lineno
#      print "syntax error, line %d, col %d, unexpected character" % (line, col)
#      print "==> "+s.split("\n")[line-1]
#      print "  "+(" "*col)+"^---- near here"

