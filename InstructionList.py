from .instructions.Instruction import Instruction
from collections import UserList
from .instructions import *
from .instructions.La import La

class InstructionList(UserList):
  def __str__(self):
    return "\n".join([str(i) for i in self.data])

  def getLast(self) -> Instruction:
    return self.data[-1]
