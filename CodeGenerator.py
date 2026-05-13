import sys
import os
from typing import List

from .CodeObject import CodeObject
from .InstructionList import InstructionList
from .instructions import *
from ..compiler import *
from ..ast import *
from ..ast.visitor.AbstractASTVisitor import AbstractASTVisitor
from ..ast.CastNode import CastNode


class CodeGenerator(AbstractASTVisitor):

    def __init__(self):
        self.intRegCount = 0
        self.floatRegCount = 0
        self.intTempPrefix = 't'
        self.floatTempPrefix = 'f'
        self.loopLabel = 0
        self.elseLabel = 0
        self.outLabel = 0
        self.currFunc = None

    def getIntRegCount(self):
        return self.intRegCount

    def getFloatRegCount(self):
        return self.floatRegCount

    def postprocessVarNode(self, node: VarNode) -> CodeObject:
        sym = node.getSymbol()

        co = CodeObject(sym)
        co.lval = True
        co.type = node.getType()

        return co

    def postprocessIntLitNode(self, node: IntLitNode) -> CodeObject:
        co = CodeObject()
        i = Li(self.generateTemp(Scope.InnerType.INT), node.getVal())

        co.code.append(i)  
        co.lval = False  
        co.temp = i.getDest()
        co.type = node.getType()  
        return co

    def postprocessFloatLitNode(self, node: FloatLitNode) -> CodeObject:
        co = CodeObject()

        i = FImm(self.generateTemp(Scope.InnerType.FLOAT), node.getVal())

        co.code.append(i)  
        co.lval = False  
        co.temp = i.getDest()  
        co.type = node.getType()
        return co

     

    def postprocessCastNode(self, node: CastNode, expr: CodeObject) -> CodeObject:

        print(f"CastNode Type Before Processing: Node Type={node.type}, Expression Type={expr.type}")

        if expr.lval:
            expr = self.rvalify(expr)

        if expr.temp is None:
            raise Exception("Child expression did not produce a valid temp in CastNode.")

        co = CodeObject()
        print(f"Child Expression Debug: expr.temp={expr.temp}, expr.type={expr.type}, expr.code={expr.code}")

        co.code.extend(expr.code)  

        source_type = expr.type
        target_type = node.getType()
        print(f"visitCastNode past the determine target type of the cast")
    
        if source_type == target_type:
            co = expr
        elif source_type == Scope.Type(Scope.InnerType.INT) and target_type == Scope.Type(Scope.InnerType.FLOAT):
            print(f"visitCastNode inside first if statement of INT and FLOAT")
            temp = self.generateTemp(Scope.InnerType.FLOAT)
            if temp is None:
                raise Exception("Failed to generate a valid temporary register for INT to FLOAT cast.")
            print(f"visitCastNode past the generateTemp for FLOAT")
            convert_instr = IMovf(expr.temp, temp) 
            co.code.append(convert_instr)
            co.temp = temp
            co.type = Scope.Type(Scope.InnerType.FLOAT)
            print(f"Cast INT to FLOAT: {convert_instr}")

        elif source_type == Scope.Type(Scope.InnerType.FLOAT) and target_type == Scope.Type(Scope.InnerType.INT):
            temp = self.generateTemp(Scope.InnerType.INT)
            if temp is None:
                raise Exception("Failed to generate a valid temporary register for INT to FLOAT cast.")
           
            convert_instr = FMovi(expr.temp, temp)  
            co.code.append(convert_instr)
            co.temp = temp
            co.type = Scope.Type(Scope.InnerType.INT)
            print(f"Cast FLOAT to INT: {convert_instr}")

        else:
            print(f"Unsupported cast from {source_type} to {target_type}")

        print(f"CastNode Output: Type={co.type}, Temp={co.temp}")

        return co

    def lpostprocessBinaryOpNode(self, node: BinaryOpNode, left: CodeObject, right: CodeObject) -> CodeObject:

        co = CodeObject()
      
        if left.lval:
            left = self.rvalify(left)
        co.code.extend(left.code)

        if right.lval:
            right = self.rvalify(right)
        co.code.extend(right.code)

        optype = node.getOp()

        if left.getType().type == Scope.InnerType.PTR:
            left_type = Scope.InnerType.INT
        else:
            left_type = left.getType().type

        if right.getType().type == Scope.InnerType.PTR:
            right_type = Scope.InnerType.INT
        else:
            right_type = right.getType().type

        if left.type == right.type:
            if node.getOp() == BinaryOpNode.OpType.ADD:
                if left_type == Scope.InnerType.FLOAT and right_type == Scope.InnerType.FLOAT:
                    dest = self.generateTemp(Scope.InnerType.FLOAT)
                    instr = FAdd(left.temp, right.temp, dest)
                elif left_type == Scope.InnerType.INT and right_type == Scope.InnerType.INT:
                    dest = self.generateTemp(Scope.InnerType.INT)
                    instr = Add(left.temp, right.temp, dest)
                else:
                    raise Exception("Unsupported operand types for ADD operation.")

            elif node.getOp() == BinaryOpNode.OpType.SUB:
                if left_type == Scope.InnerType.FLOAT and right_type == Scope.InnerType.FLOAT:
                    dest = self.generateTemp(Scope.InnerType.FLOAT)
                    instr = FSub(left.temp, right.temp, dest)
                elif left_type == Scope.InnerType.INT and right_type == Scope.InnerType.INT:
                    dest = self.generateTemp(Scope.InnerType.INT)
                    instr = Sub(left.temp, right.temp, dest)
                else:
                    raise Exception("Unsupported operand types for SUB operation.")

            elif node.getOp() == BinaryOpNode.OpType.MUL:
                if left_type == Scope.InnerType.FLOAT and right_type == Scope.InnerType.FLOAT:
                    dest = self.generateTemp(Scope.InnerType.FLOAT)
                    instr = FMul(left.temp, right.temp, dest)
                elif left_type == Scope.InnerType.INT and right_type == Scope.InnerType.INT:
                    dest = self.generateTemp(Scope.InnerType.INT)
                    instr = Mul(left.temp, right.temp, dest)
                else:
                    raise Exception("Unsupported operand types for MUL operation.")
            elif node.getOp() == BinaryOpNode.OpType.DIV:
                if left_type == Scope.InnerType.FLOAT and right_type == Scope.InnerType.FLOAT:
                    dest = self.generateTemp(Scope.InnerType.FLOAT)
                    instr = FDiv(left.temp, right.temp, dest)
                elif left_type == Scope.InnerType.INT and right_type == Scope.InnerType.INT:
                    dest = self.generateTemp(Scope.InnerType.INT)
                    instr = Div(left.temp, right.temp, dest)
                else:
                    raise Exception("Unsupported operand types for DIV operation.")
            else:
                raise Exception(f"Unsupported binary operator: {node.getOp()}")

            co.code.append(instr)
            co.temp = instr.getDest()
            co.lval = False
            co.type = left.type 

        else:
            if left_type == Scope.InnerType.INT and right_type == Scope.InnerType.FLOAT:
                promoted_left_temp = self.generateTemp(Scope.InnerType.FLOAT)
                co.code.append(IMovf(left.temp, promoted_left_temp))
                left.temp = promoted_left_temp
                left_type = Scope.InnerType.FLOAT
            elif left_type == Scope.InnerType.FLOAT and right_type == Scope.InnerType.INT:
                promoted_right_temp = self.generateTemp(Scope.InnerType.FLOAT)
                co.code.append(IMovf(right.temp, promoted_right_temp))
                right.temp = promoted_right_temp
                right_type = Scope.InnerType.FLOAT

            elif left_type == Scope.InnerType.PTR and right_type == Scope.InnerType.INT:
                pass

            elif right_type == Scope.InnerType.PTR and left_type == Scope.InnerType.INT:
                pass

            elif left_type == Scope.InnerType.PTR or right_type == Scope.InnerType.PTR:
                raise Exception(
                    "Unsupported pointer arithmetic involving two pointers or mixed types that are not supported.")

            else:
                raise Exception("Unsupported operand type or pointer arithmetic")
            result_temp = self.generateTemp(Scope.InnerType.FLOAT)
            if optype == BinaryOpNode.OpType.ADD:
                instr = FAdd(left.temp, right.temp, result_temp)
            elif optype == BinaryOpNode.OpType.SUB:
                instr = FSub(left.temp, right.temp, result_temp)
            elif optype == BinaryOpNode.OpType.MUL:
                instr = FMul(left.temp, right.temp, result_temp)
            elif optype == BinaryOpNode.OpType.DIV:
                instr = FDiv(left.temp, right.temp, result_temp)
            else:
                raise Exception(f"Unsupported binary operator: {optype}")

            co.code.append(instr)
            co.temp = instr.getDest()
            co.type = Scope.Type(Scope.InnerType.FLOAT)

        co.lval = False
        print(f"BinaryOpNode Output Code: {co.code}")
        print(f"BinaryOpNode Final Temp: {co.temp}")
        print(f"BinaryOpNode Output: Left Temp={left.temp}, Right Temp={right.temp}, Type={co.type}")

        return co

    def postprocessBinaryOpNode(self, node: BinaryOpNode, left: CodeObject, right: CodeObject) -> CodeObject:
        co = CodeObject()
        if left.lval is True:
            left = self.rvalify(left)
            
        co.code.extend(left.code)

        if right.lval is True:
            right = self.rvalify(right)

        co.code.extend(right.code)

        optype = node.getOp()

        if left.getType().type == Scope.InnerType.PTR:
            left_type = Scope.InnerType.INT  
        else:
            left_type = left.getType().type

        if right.getType().type == Scope.InnerType.PTR:
            right_type = Scope.InnerType.INT  
        else:
            right_type = right.getType().type

        if left_type == Scope.InnerType.INT and right_type == Scope.InnerType.FLOAT:
            promoted_left_temp = self.generateTemp(Scope.InnerType.FLOAT)
            co.code.append(IMovf(left.temp, promoted_left_temp))
            left.temp = promoted_left_temp
            left_type = Scope.InnerType.FLOAT
        elif left_type == Scope.InnerType.FLOAT and right_type == Scope.InnerType.INT:
            promoted_right_temp = self.generateTemp(Scope.InnerType.FLOAT)
            co.code.append(IMovf(right.temp, promoted_right_temp))
            right.temp = promoted_right_temp
            right_type = Scope.InnerType.FLOAT

        if optype == BinaryOpNode.OpType.ADD:
            if left_type == Scope.InnerType.FLOAT and right_type == Scope.InnerType.FLOAT:
                dest = self.generateTemp(Scope.InnerType.FLOAT)
                instr = FAdd(left.temp, right.temp, dest)
            elif left_type == Scope.InnerType.INT and right_type == Scope.InnerType.INT:
                dest = self.generateTemp(Scope.InnerType.INT)
                instr = Add(left.temp, right.temp, dest)
            else:
                raise Exception("Unsupported operand types for ADD operation.")
        elif optype == BinaryOpNode.OpType.SUB:
            if left_type == Scope.InnerType.FLOAT and right_type == Scope.InnerType.FLOAT:
                dest = self.generateTemp(Scope.InnerType.FLOAT)
                instr = FSub(left.temp, right.temp, dest)
            elif left_type == Scope.InnerType.INT and right_type == Scope.InnerType.INT:
                dest = self.generateTemp(Scope.InnerType.INT)
                instr = Sub(left.temp, right.temp, dest)
            else:
                raise Exception("Unsupported operand types for SUB operation.")
        elif optype == BinaryOpNode.OpType.MUL:
            if left_type == Scope.InnerType.FLOAT and right_type == Scope.InnerType.FLOAT:
                dest = self.generateTemp(Scope.InnerType.FLOAT)
                instr = FMul(left.temp, right.temp, dest)
            elif left_type == Scope.InnerType.INT and right_type == Scope.InnerType.INT:
                dest = self.generateTemp(Scope.InnerType.INT)
                instr = Mul(left.temp, right.temp, dest)
            else:
                raise Exception("Unsupported operand types for MUL operation.")
        elif optype == BinaryOpNode.OpType.DIV:
            if left_type == Scope.InnerType.FLOAT and right_type == Scope.InnerType.FLOAT:
                dest = self.generateTemp(Scope.InnerType.FLOAT)
                instr = FDiv(left.temp, right.temp, dest)
            elif left_type == Scope.InnerType.INT and right_type == Scope.InnerType.INT:
                dest = self.generateTemp(Scope.InnerType.INT)
                instr = Div(left.temp, right.temp, dest)
            else:
                raise Exception("Unsupported operand types for DIV operation.")
        else:
            raise Exception(f"Unsupported binary operator: {optype}")

        co.code.append(instr)

        co.temp = instr.getDest()
        co.lval = False
        co.type = Scope.Type(left_type) 

        return co

    def postprocessUnaryOpNode(self, node: UnaryOpNode, expr: CodeObject) -> CodeObject:
        co = CodeObject()
       
        if expr.lval:
            expr = self.rvalify(expr)
            co.code.extend(expr.code)
        else:
            co.code.extend(expr.code)
        if node.getOp() == UnaryOpNode.OpType.NEG:
            instr = Neg(expr.temp, self.generateTemp(expr.type.type))  
            co.code.append(instr)
            co.temp = instr.getDest() 

        co.lval = False

        return co

    def postprocessAssignNode(self, node: AssignNode, left: CodeObject, right: CodeObject) -> CodeObject:

        co = CodeObject()

        print(f"assign node enter")
        print(f"AssignNode Input: Left Temp = {left.temp}, Left Type = {left.type}")
        print(f"AssignNode Input: Right Temp = {right.temp}, Right Type = {right.type}, Right Code = {right.code}")

        if left.isVar() and not left.getSTE().isLocal():
            left_instruction_list = self.generateAddrFromVariable(left)
            co.code.extend(left_instruction_list)
            left.temp = left_instruction_list[-1].getDest()  
        else:
            co.code.extend(left.code)

        if right.lval:
            right = self.rvalify(right)

        co.code.extend(right.code)

        if right.lval:
            if right.getSTE() is not None: 
                if right.getType() is None:
                    raise Exception("Right-hand side has no type")
                if right.getType().type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
                    load_instr = Lw(self.generateTemp(right.getType().type), "fp", right.getSTE().addressToString())
                else:
                    load_instr = Flw(self.generateTemp(right.getType().type), "fp", right.getSTE().addressToString())
            else: 
                if right.getType() is None:
                    raise Exception("Right-hand side has no type for temporary variable")
                if right.getType().type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
                    load_instr = Lw(self.generateTemp(right.getType().type), right.temp, "0")
                else:
                    load_instr = Flw(self.generateTemp(right.getType().type), right.temp, "0")

            co.code.append(load_instr)
            right.temp = load_instr.getDest()

        if left.type != right.type: 
            print(f"Type mismatch detected: Left Type={left.type}, Right Type={right.type}")
            if left.type == Scope.Type(Scope.InnerType.INT) and right.type == Scope.Type(Scope.InnerType.FLOAT):
                print(f"Promoting FLOAT {right.temp} to INT for assignment")

                promoted_temp = self.generateTemp(Scope.InnerType.INT)

                co.code.append(FMovi(right.temp, promoted_temp))
                right.temp = promoted_temp

                print(f"Promotion complete: New Temp={right.temp}")


            elif left.type == Scope.Type(Scope.InnerType.FLOAT) and right.type == Scope.Type(Scope.InnerType.INT):
                print(f"Demoting INT {right.temp} to FLOAT for assignment")
                demoted_temp = self.generateTemp(Scope.InnerType.FLOAT)
                co.code.append(IMovf(right.temp, demoted_temp))
                right.temp = demoted_temp
                print(f"Demotion complete: New Temp={right.temp}")

        print(f"AssignNode Debug: Final CodeObject before store: Temp={co.temp}, Type={co.type}, Code={co.code}")

        if left.getType().type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
            if left.isVar() and left.getSTE().isLocal():
                instr = Sw(right.temp, "fp", str(left.getSTE().addressToString()))
            else:
                instr = Sw(right.temp, left.temp, "0")
            co.temp = instr.getDest()
            co.code.append(instr)
            print(f"Stored INT/PTR: Instruction={instr}, Updated Temp={co.temp}")
        elif left.getType().type == Scope.InnerType.FLOAT:
            if left.isVar() and left.getSTE().isLocal():
                instr = Fsw(right.temp, "fp", str(left.getSTE().addressToString()))
            else:
                instr = Fsw(right.temp, left.temp, "0")
            co.temp = instr.getDest()
            co.code.append(instr)
            print(f"Stored FLOAT: Instruction={instr}, Updated Temp={co.temp}")

        print(f"AssignNode Output: Left Temp = {left.temp}, Right Temp = {right.temp}, Code = {co.code}")
        co.temp = right.temp
        co.type = right.type
        return co

    def debugpostprocessBinaryOpNode(self, node, left, right):
        co = CodeObject()
        print(f"BinaryOpNode Input: Left Temp={left.temp}, Right Temp={right.temp}")

        if left.lval:
            left = self.rvalify(left)
        if left.temp is None:
            raise Exception("Left operand in BinaryOpNode did not produce a valid temp.")
        co.code.extend(left.code)
        
        if right.lval:
            right = self.rvalify(right)
        if right.temp is None:
            raise Exception("Right operand in BinaryOpNode did not produce a valid temp.")
        co.code.extend(right.code)

        if left.type is None or right.type is None:
            raise Exception("Left or right operand type is None.")

        print(f"BinaryOpNode After Rvalify: Left Temp={left.temp}, Right Temp={right.temp}")

        optype = node.getOp()
        result_temp = self.generateTemp(
            Scope.InnerType.FLOAT if left.type == Scope.InnerType.FLOAT or right.type == Scope.InnerType.FLOAT else Scope.InnerType.INT)

        if result_temp is None:
            raise Exception("Failed to generate a result temp for BinaryOpNode.")

        if optype == BinaryOpNode.OpType.ADD:
            if left.type == Scope.InnerType.FLOAT or right.type == Scope.InnerType.FLOAT:
                instr = FAdd(left.temp, right.temp, result_temp)
            else:
                instr = Add(left.temp, right.temp, result_temp)
        else:
            raise Exception(f"Unsupported binary operation type: {optype}")

        co.code.append(instr)
        co.temp = instr.getDest()
        co.lval = False
        co.type = Scope.Type(
            Scope.InnerType.FLOAT if left.type == Scope.InnerType.FLOAT or right.type == Scope.InnerType.FLOAT else Scope.InnerType.INT)

        print(f"BinaryOpNode Final Temp: {co.temp}, Final Code: {co.code}")

        return co

    def debugpostprocessCastNode(self, node, expr):
        if expr.temp is None:
            print("CastNode found expr without a valid temp. Forcing temp generation.")
            expr.temp = self.generateTemp(expr.getType().type)

        return expr

    def debugpostprocessAssignNode(self, node, left, right):
        co = CodeObject()
        print(
            f"AssignNode Input: Left Temp={left.temp}, Left Type={left.type}, Right Temp={right.temp}, Right Type={right.type}")

        if left.temp is None:
            if left.type is None:
                raise Exception("Left operand type is None, cannot generate temp.")
            if not isinstance(left.type, Scope.Type):
                raise Exception(f"Unexpected type for left operand: {left.type}. Expected Scope.Type.")
            left.temp = self.generateTemp(left.type.type)

        co.code.extend(right.code)

        if left.type != right.type:
            print(f"Type mismatch in AssignNode: promoting/demoting types.")
            if left.type == Scope.Type(Scope.InnerType.FLOAT) and right.type == Scope.Type(Scope.InnerType.INT):
                promoted_temp = self.generateTemp(Scope.InnerType.FLOAT)
                co.code.append(IMovf(right.temp, promoted_temp))
                right.temp = promoted_temp
            elif left.type == Scope.Type(Scope.InnerType.INT) and right.type == Scope.Type(Scope.InnerType.FLOAT):
                demoted_temp = self.generateTemp(Scope.InnerType.INT)
                co.code.append(FMovi(right.temp, demoted_temp))
                right.temp = demoted_temp
            else:
                raise Exception("Unsupported type conversion in AssignNode")

        if left.getSTE() is not None and left.getSTE().isLocal():
            instr = Sw(right.temp, "fp", left.getSTE().addressToString())
        else:
            instr = Sw(right.temp, left.temp, "0")
        co.code.append(instr)

        co.temp = right.temp
        co.type = right.type

        print(f"AssignNode Output Code: {co.code}")

        return co

    def postprocessStatementListNode(self, node: StatementListNode, statements: list) -> CodeObject:
        co = CodeObject()

        for subcode in statements:
            co.code.extend(subcode.code)

        co.type = None
        return co

    def postprocessReadNode(self, node: ReadNode, var: CodeObject) -> CodeObject:
        co = CodeObject()
        assert (var.getSTE() is not None)

        il = InstructionList()

        typ = node.getType()

        if typ.type == Scope.InnerType.INT:
            geti = GetI(self.generateTemp(Scope.InnerType.INT))
            il.append(geti)
            store = InstructionList()
            if var.getSTE().isLocal():
                store.append(Sw(geti.getDest(), "fp", var.getSTE().addressToString()))
            else:
                store.extend(self.generateAddrFromVariable(var))
                store.append(Sw(geti.getDest(), store.getLast().getDest(), "0"))
            il.extend(store)
        elif typ.type == Scope.InnerType.FLOAT:
            getf = GetF(self.generateTemp(Scope.InnerType.FLOAT))
            il.append(getf)
            fstore = InstructionList()
            if var.getSTE().isLocal():
                fstore.append(Fsw(getf.getDest(), "fp", var.getSTE().addressToString()))
            else:
                fstore.extend(self.generateAddrFromVariable(var))
                fstore.append(Fsw(getf.getDest(), fstore.getLast().getDest(), "0"))
            il.extend(fstore)
        else:
            raise Exception("Shouldn't read into other variable")

        co.code.extend(il)

        co.lval = False 
        co.temp = None  
        co.type = None  

        return co

    def postprocessWriteNode(self, node: WriteNode, expr: CodeObject) -> CodeObject:
        co = CodeObject()

        if node.getWriteExpr().getType().type == Scope.InnerType.STRING:
            assert (expr.getSTE() is not None)

            addrCo = self.generateAddrFromVariable(expr)
            co.code.extend(addrCo)

            write = PutS(addrCo.getLast().getDest())
            co.code.append(write)
        else:
            if expr.lval is True:
                expr = self.rvalify(expr)

            co.code.extend(expr.code)

            write = None
            typ = node.getWriteExpr().getType()
            if typ.type == Scope.InnerType.STRING:
                raise Exception("Shouldn't have a STRING here")
            elif typ.type == Scope.InnerType.INT or typ.type == Scope.InnerType.PTR:
                write = PutI(expr.temp)
            elif typ.type == Scope.InnerType.FLOAT:
                write = PutF(expr.temp)
            else:
                raise Exception("WriteNode has a weird type")
            co.code.append(write)

        co.lval = False  
        co.temp = None  
        co.type = None  
        return co

    def postprocessCondNode(self, node: CondNode, left: CodeObject, right: CodeObject) -> CodeObject:
        co = CodeObject()
        
        if left.lval:
            left = self.rvalify(left)
        co.code.extend(left.code)

        if right.lval:
            right = self.rvalify(right)
        co.code.extend(right.code)
t
        co.ltemp = left.temp 
        co.rtemp = right.temp  

        if left.getType().type == Scope.InnerType.INT and right.getType().type == Scope.InnerType.INT:
            co.type = Scope.Type(Scope.InnerType.INT)

        elif left.type == Scope.Type(Scope.InnerType.FLOAT) and right.type == Scope.Type(Scope.InnerType.FLOAT):
            co.type = Scope.Type(Scope.InnerType.FLOAT)

        else:
            raise ValueError(f"Incompatible operand types for CondNode: {left.type} and {right.type}")

        op = node.getOp()

        if op == CondNode.OpType.LT:
            co.cond_type = "<"
        elif op == CondNode.OpType.LE:
            co.cond_type = "<="
        elif op == CondNode.OpType.GT:
            co.cond_type = ">"
        elif op == CondNode.OpType.GE:
            co.cond_type = ">="
        elif op == CondNode.OpType.EQ:
            co.cond_type = "=="
        elif op == CondNode.OpType.NE:
            co.cond_type = "!="
        else:
            raise ValueError(f"Unsupported operator: {op}")

        co.lval = False  
        co.temp = None
        co.conop = co.cond_type

        return co

    def postprocessIfStatementNode(self, node: IfStatementNode, cond: CodeObject, tlist: CodeObject,
                                   elist: CodeObject) -> CodeObject:
        co = CodeObject()
                                       
        else_present = elist and elist.code
        else_label = self.generateElseLabel() if else_present else self.generateOutLabel()
        out_label = self.generateOutLabel()
        temp_float = self.generateTemp(Scope.InnerType.INT)

        co.code.extend(cond.code)

        comp = None

        if cond.type.type == Scope.InnerType.INT:
            op = cond.cond_type 
            if op == "==":
                comp = Bne(cond.ltemp, cond.rtemp, else_label)
            elif op == "!=":
                comp = Beq(cond.ltemp, cond.rtemp, else_label)
            elif op == "<":
                comp = Bge(cond.ltemp, cond.rtemp, else_label)
            elif op == ">":
                comp = Ble(cond.ltemp, cond.rtemp, else_label)
            elif op == "<=":
                comp = Bgt(cond.ltemp, cond.rtemp, else_label)
            elif op == ">=":
                comp = Blt(cond.ltemp, cond.rtemp, else_label)
        elif cond.type.type == Scope.InnerType.FLOAT:
            op = cond.cond_type
            if op == "==":
                comp = Feq(cond.ltemp, cond.rtemp, temp_float)
                co.code.append(comp)
                comp = Beq(temp_float, "x0", else_label)
            elif op == "!=":
                comp = Feq(cond.ltemp, cond.rtemp, temp_float)
                co.code.append(comp)
                comp = Bne(temp_float, "x0", else_label)
            elif op == "<":
                comp = Flt(cond.ltemp, cond.rtemp, temp_float)
                co.code.append(comp)
                comp = Beq(temp_float, "x0", else_label)
            elif op == ">":
                comp = Flt(cond.ltemp, cond.rtemp, temp_float)
                co.code.append(comp)
                comp = Beq(temp_float, "x0", else_label)
            elif op == "<=":
                comp = Fle(cond.ltemp, cond.rtemp, temp_float)
                co.code.append(comp)
                comp = Beq(temp_float, "x0", else_label)
            elif op == ">=":
                comp = Fle(cond.ltemp, cond.rtemp, temp_float)
                co.code.append(comp)
                comp = Beq(temp_float, "x0", else_label)

        co.code.append(comp)

        co.code.extend(tlist.code) \
 \
       
        co.code.append(J(out_label))

 
        co.code.append(Label(else_label))
        if elist:
            co.code.extend(elist.code)
        co.code.append(Label(out_label))

        return co

    def postprocessWhileNode(self, node: WhileNode, cond: CodeObject, wlist:
    CodeObject) -> CodeObject:
        co = CodeObject()
    
        loop_label = self.generateLoopLabel()
        exit_label = self.generateOutLabel()

        co.code.append(Label(loop_label))

        co.code.extend(cond.code)

        branch_inst = None

        if cond.type.type == Scope.InnerType.INT:
            op = cond.cond_type  
            if op == "==":
                branch_inst = Bne(cond.ltemp, cond.rtemp, exit_label)
            elif op == "!=":
                branch_inst = Beq(cond.ltemp, cond.rtemp, exit_label)
            elif op == "<":
                branch_inst = Bge(cond.ltemp, cond.rtemp, exit_label)
            elif op == "<=":
                branch_inst = Bgt(cond.ltemp, cond.rtemp, exit_label)
            elif op == ">":
                branch_inst = Ble(cond.ltemp, cond.rtemp, exit_label)
            elif op == ">=":
                branch_inst = Blt(cond.ltemp, cond.rtemp, exit_label)
            else:
                raise ValueError(f"Invalid operator for INT type: {op}")

        elif cond.type.type == Scope.InnerType.FLOAT:
            temp_float = self.generateTemp(Scope.InnerType.INT)
            op = cond.cond_type
            if op == "==":
                branch_inst = Feq(cond.ltemp, cond.rtemp, temp_float)
                co.code.append(branch_inst)
                branch_inst = Beq(temp_float, "x0", exit_label)
            elif op == "!=":
                branch_inst = Feq(cond.ltemp, cond.rtemp, temp_float)
                co.code.append(branch_inst)
                branch_inst = Bne(temp_float, "x0", exit_label)
            elif op == "<":
                branch_inst = Flt(cond.ltemp, cond.rtemp, temp_float)
                co.code.append(branch_inst)
                branch_inst = Beq(temp_float, "x0", exit_label)
            elif op == "<=":
                branch_inst = Fle(cond.ltemp, cond.rtemp, temp_float)
                co.code.append(branch_inst)
                branch_inst = Bne(temp_float, "x0", exit_label)
            elif op == ">":
                branch_inst = Flt(cond.ltemp, cond.rtemp, temp_float)
                co.code.append(branch_inst)
                branch_inst = Beq(temp_float, "x0", exit_label)
            elif op == ">=":
                branch_inst = Fle(cond.ltemp, cond.rtemp, temp_float)
                co.code.append(branch_inst)
                branch_inst = Bne(temp_float, "x0", exit_label)
            else:
                raise ValueError(f"Invalid operator for FLOAT type: {op}")

        else:
            raise ValueError(f"Unsupported type for condition: {cond.type.type}")

 
        co.code.append(branch_inst)


        co.code.extend(wlist.code)


        co.code.append(J(loop_label))


        co.code.append(Label(exit_label))

        return co
        
    def postprocessReturnNode(self, node: ReturnNode, retExpr: CodeObject) -> CodeObject:
        co = CodeObject()

        if retExpr is None:
            return co

        if retExpr.lval:
            retExpr = self.rvalify(retExpr)
        co.code.extend(retExpr.code)

        if retExpr.getType().type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
            i = Sw(retExpr.temp, "fp", "8")  
            co.code.append(i)
        elif retExpr.getType().type == Scope.InnerType.FLOAT:
            i = Fsw(retExpr.temp, "fp", "8") 
            co.code.append(i)

        i = J(self.generateFunctionOutLabel())
        co.code.append(i)

        return co

    def preprocessFunctionNode(self, node: FunctionNode):

        self.currFunc = node.getFuncName()

        self.intRegCount = 0
        self.floatRegCount = 0

    def postprocessFunctionNode(self, node: FunctionNode, body: CodeObject) -> CodeObject:
        co = CodeObject()

        i = Label("func_" + node.getFuncName())
        co.code.append(i)

        i = Sw("fp", "sp", "0") 
        co.code.append(i)

        i = Mv("sp", "fp") 
        co.code.append(i)

     
        i = Addi("sp", "-4", "sp")
        co.code.append(i)

      
        i = Addi("sp", str(node.getScope().getNumLocals() * -4), "sp")  
        co.code.append(i)

       
        int_count = self.getIntRegCount()  
        float_count = self.getFloatRegCount()  

        for val in range(1, int_count + 1):
            co.code.extend(self.pushRegister(f"t{val}", Scope.Type(Scope.InnerType.INT)).code)

        # Save float registers
        for val in range(1, float_count + 1):
            co.code.extend(self.pushRegister(f"f{val}", Scope.Type(Scope.InnerType.FLOAT)).code)

        # Step 5: Add the code from the function body
        co.code.extend(body.code)

        # Step 6: Post-processing code
        # Step 6a: Label for `return` statements inside function body to jump to
        i = Label("func_ret_" + node.getFuncName())
        co.code.append(i)

        for val in range(1, float_count + 1):
           
            co.code.extend(self.popRegister(f"f{float_count + 1 - val}", Scope.Type(Scope.InnerType.FLOAT)).code)

        for val in range(1, int_count + 1):
            co.code.extend(self.popRegister(f"t{int_count + 1 - val}", Scope.Type(Scope.InnerType.INT)).code)

        i = Mv("fp", "sp") 
        co.code.append(i)

        i = Lw("fp", "fp", "0")  
        co.code.append(i)

        i = Ret() 
        co.code.append(i)

        return co

    def postprocessFunctionListNode(self, node: FunctionListNode, functions: List[CodeObject]) -> CodeObject:
        co = CodeObject()

        co.code.append(Mv("sp", "fp"))
        co.code.append(Jr(self.generateFunctionLabel("main")))
        co.code.append(Halt())
        co.code.append(Blank())

        for c in functions:
            co.code.extend(c.code)
            co.code.append(Blank())

        return co

    def postprocessCallNode(self, node: CallNode, args: List[CodeObject]) -> CodeObject:
        co = CodeObject()
  
        for codeobj in args:

            if codeobj.lval:
                codeobj = self.rvalify(codeobj)
            co.code.extend(codeobj.code)

            co.code.extend(self.pushRegister(codeobj.temp, codeobj.getType()).code)

        i = Addi("sp", "-4", "sp")
        co.code.append(i)
  
        co.code.extend(self.pushRegister("ra", Scope.Type(Scope.InnerType.INT)).code)

        func_name = node.getFuncName()
        i = Jr("func_" + func_name)
        co.code.append(i)
      
        co.code.extend(self.popRegister("ra", Scope.Type(Scope.InnerType.INT)).code)

        return_type = node.getType().type

        if return_type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
            codeObj = self.popRegister(self.generateTemp(Scope.InnerType.INT), Scope.Type(Scope.InnerType.INT))
            co.code.extend(codeObj.code)
            co.temp = codeObj.code[-1].getDest() 
        elif return_type == Scope.InnerType.FLOAT:
            codeObj = self.popRegister(self.generateTemp(Scope.InnerType.FLOAT), Scope.Type(Scope.InnerType.FLOAT))
            co.code.extend(codeObj.code)
            co.temp = codeObj.code[-1].getDest()
        elif return_type == Scope.InnerType.VOID:
            i = Addi("sp", "4", "sp") 
            co.code.append(i)

        i = Addi("sp", str(len(args) * 4), "sp")
        co.code.append(i)

        co.type = node.getType()

        return co

    def pushRegister(self, register: str, reg_type: Scope.Type) -> CodeObject:
        co = CodeObject()

        if reg_type.type == Scope.InnerType.PTR:
    
            co_type = Scope.InnerType.INT 
        else:
            co_type = reg_type.type
            
        if co_type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
            instr = Sw(register, "sp", "0")  
            co.code.append(instr)
        elif co_type == Scope.InnerType.FLOAT:
            instr = Fsw(register, "sp", "0") 
            co.code.append(instr)


        i = Addi("sp", "-4", "sp")
        co.code.append(i)

        return co

    def popRegister(self, register: str, reg_type: Scope.Type) -> CodeObject:
        co = CodeObject()

        i = Addi("sp", "4", "sp")
        co.code.append(i)

        if reg_type.type == Scope.InnerType.INT:
            i = Lw(register, "sp", "0")
            co.code.append(i)
            co.temp = i.getDest()
      
        elif reg_type.type == Scope.InnerType.FLOAT:
            i = Flw(register, "sp", "0")
            co.code.append(i)
            co.temp = i.getDest()

        return co

    def postprocessPtrDerefNode(self, node: PtrDerefNode, expr: CodeObject) -> CodeObject:

        co = CodeObject()

        if expr.lval:  
            expr = self.rvalify(expr)

        co.code.extend(expr.code) 

        co.temp = expr.temp 
        co.lval = True  
        co.type = node.getType()

        return co
        
    def postprocessAddrOfNode(self, node: AddrOfNode, expr: CodeObject) -> CodeObject:
        co = CodeObject()
        if expr.isVar():
            addr_instructions = self.generateAddrFromVariable(expr)
            co.code.extend(addr_instructions)
            expr.temp = addr_instructions.getLast().getDest()
        co.code.extend(expr.code)
        co.temp = expr.temp
        co.lval = False
        co.type = node.getType()
        return co

    def postprocessMallocNode(self, node: MallocNode, expr: CodeObject) -> CodeObject:
        co = CodeObject()
        
        if expr.lval:
            expr = self.rvalify(expr)
        co.code.extend(expr.code)

        dest = self.generateTemp(expr.getType().type) 
        malloc_instr = Malloc(expr.temp, dest)  
        co.code.append(malloc_instr)

        co.temp = dest
        co.type = Scope.Type(Scope.InnerType.PTR)
        co.lval = False 

        return co

    def postprocessFreeNode(self, node: FreeNode, expr: CodeObject) -> CodeObject:

        co = CodeObject()

        if expr.lval:
            expr = self.rvalify(expr)
        co.code.extend(expr.code)

        free_instr = Free(expr.temp)
        co.code.append(free_instr)

        return co

    def generateTemp(self, t: Scope.InnerType) -> str:
        if t == Scope.InnerType.INT or t == Scope.InnerType.PTR:
            s = self.intTempPrefix + str(self.intRegCount + 1)
            self.intRegCount += 1
            return s
        elif t == Scope.InnerType.FLOAT:
            s = self.floatTempPrefix + str(self.floatRegCount + 1)
            self.floatRegCount += 1
            return s
        else:
            raise Exception("Generating temp for bad type")

    def generateLoopLabel(self) -> str:
        self.loopLabel += 1
        return "loop_" + str(self.loopLabel)

    def generateElseLabel(self) -> str:
        self.elseLabel += 1
        return "else_" + str(self.elseLabel)

    def generateOutLabel(self) -> str:
        self.outLabel += 1
        return "out_" + str(self.outLabel)

    def generateFunctionLabel(self, func=None) -> str:
        if func is None:
            return "func_" + self.currFunc
        else:
            return "func_" + func

    def generateFunctionOutLabel(self) -> str:
        return "func_ret_" + self.currFunc

    def rvalify(self, lco: CodeObject) -> CodeObject:
        assert (lco.lval is True)
        co = CodeObject()

        ste_is_null = lco.getSTE() is None

        co.code.extend(lco.code)

        co_type = lco.getType().type

        if ste_is_null:

            if co_type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
                load_instr = Lw(self.generateTemp(co_type), lco.temp, "0")
            else:
                load_instr = Flw(self.generateTemp(co_type), lco.temp, "0")
        else:
 
            symbol = lco.getSTE()
            address = symbol.addressToString()

            if co_type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
                load_instr = Lw(self.generateTemp(co_type), "fp", address)
            else:
                load_instr = Flw(self.generateTemp(co_type), "fp", address)

        co.code.append(load_instr)

 
        co.temp = load_instr.getDest()
        co.lval = False
        co.type = lco.getType()

        return co

    def generateAddrFromVariable(self, lco: CodeObject) -> InstructionList:

        il = InstructionList()
  
        symbol = lco.getSTE()
        address = symbol.addressToString()
    
        if symbol.isLocal():
      
            compAddr = Addi("fp", address, self.generateTemp(Scope.InnerType.INT))
        else:
            compAddr = La(self.generateTemp(Scope.InnerType.INT), address)
        il.append(compAddr)

        return il
