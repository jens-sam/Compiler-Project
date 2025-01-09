import sys
import os

from ..compiler import *
from .instructions.Instruction import Instruction
from .InstructionList import InstructionList


class CodeObject:
    def __init__(self, ste: Scope.SymbolTableEntry = None):
        self.ste = ste
        if ste is not None:
            self.type = ste.getType()
        else:
            self.type = None
        self.code = InstructionList()
        self.temp = None
        self.lval = None

        # Add these attributes
        self.cond_type = None  # For storing the condition type (e.g., "==", "<", etc.)
        self.ltemp = None  # Temporary for the left operand
        self.rtemp = None  # Temporary for the right operand

        # # Debug
        # print(
        #     f"DEBUG: CodeObject initialized with STE={self.ste}, Type={self.type}, Temp={self.temp}, Lval={self.lval}")

    def __str__(self):
        sb = ";Current temp: " + (self.temp if self.temp is not None else "") + "\n" + ";IR Code: \n" + str(self.code)
        return sb

    def getCode(self):
        return self.code

    def getTemp(self):
        # if self.temp is None:
        #     print("DEBUG: getTemp called but temp is None!")
        return self.temp

    def isVar(self):
        # result = self.ste is not None
        # print(f"DEBUG: isVar={result}, STE={self.ste}")
        return self.ste is not None

    def getSTE(self):
        return self.ste

    def getType(self):
        return self.type
