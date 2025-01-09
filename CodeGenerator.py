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

    # Generate code for Variables
    #
    # Create a code object that just holds a variable
    # Important: add a pointer from the code object to the symbol table entry so
    # we know how to generate code for it later (we'll need it to find the
    # address)
    #
    # Mark the code object as holding a variable, and also as an lval

    def postprocessVarNode(self, node: VarNode) -> CodeObject:
        sym = node.getSymbol()

        co = CodeObject(sym)
        co.lval = True
        co.type = node.getType()

        return co

    # Generate code for IntLiterals
    #
    # Use load immediate instruction to do this

    def postprocessIntLitNode(self, node: IntLitNode) -> CodeObject:
        co = CodeObject()
        i = Li(self.generateTemp(Scope.InnerType.INT), node.getVal())

        # Load an immediate into a register
        # The li and la instructions are the same, but it's helpful to distinguish
        # for readability purposes.
        # li tmp' value

        co.code.append(i)  # add this instruction to the code object
        co.lval = False  # co holds an rval -- data
        co.temp = i.getDest()
        co.type = node.getType()  # temp is in destination of li
        return co

    # Generate code for FloatLiterals
    #
    # Use load immediate instruction to do this

    def postprocessFloatLitNode(self, node: FloatLitNode) -> CodeObject:
        co = CodeObject()

        # Load an immediate into a register
        # The li and la instructions are the same, but it's helpful to distinguish
        # for readability purposes.
        # li tmp' value
        i = FImm(self.generateTemp(Scope.InnerType.FLOAT), node.getVal())

        co.code.append(i)  # add this instruction to the code object
        co.lval = False  # co holds an rval -- data
        co.temp = i.getDest()  # temp is in destination of li
        co.type = node.getType()
        return co

        # Generate code for binary operations.
        #
        # Step 0: create new code object
        # Step 1: add code from left child
        # Step 1a: if left child is an lval, add a load to get the data
        # Step 2: add code from right child
        # Step 2a: if right child is an lval, add a load to get the data
        # Step 3: generate binary operation using temps from left and right
        #
        # Don't forget to update the temp and lval fields of the code object!
        # 	   Hint: where is the result stored? Is this data or an address?

    # MINE
    #   this is for my new CastNode Class

    # def preprocessCastNode(self, node: CastNode):
    #     expr = node.getExpr().accept(self)
    #     print(f"Preprocessing CastNode: Child Expr Temp={expr.temp}, Type={expr.type}, Code={expr.code}")
    #     if expr.temp is None:
    #         raise Exception(f"CastNode child expression did not produce a valid temp. Node: {node}, Expr: {expr}")
    #     return expr

    def postprocessCastNode(self, node: CastNode, expr: CodeObject) -> CodeObject:


        # Preprocess the child expression first
        # expr = self.preprocessCastNode(node)
        # Validate the child expression
        # Debug: Print types before proceeding
        print(f"CastNode Type Before Processing: Node Type={node.type}, Expression Type={expr.type}")

        if expr.lval:
            expr = self.rvalify(expr)

        if expr.temp is None:
            raise Exception("Child expression did not produce a valid temp in CastNode.")

        # Create a new CodeObject for the cast
        co = CodeObject()
        print(f"Child Expression Debug: expr.temp={expr.temp}, expr.type={expr.type}, expr.code={expr.code}")

        co.code.extend(expr.code)  # Copy existing code

        # Determine the target type of the cast
        source_type = expr.type
        target_type = node.getType()
        print(f"visitCastNode past the determine target type of the cast")
        # if expr.temp is None:
        #     raise Exception("Child expression did not produce a valid temp")
        if source_type == target_type:
            # No casting needed, directly use the original expr
            co = expr
        elif source_type == Scope.Type(Scope.InnerType.INT) and target_type == Scope.Type(Scope.InnerType.FLOAT):
            print(f"visitCastNode inside first if statement of INT and FLOAT")
            # Cast INT -> FLOAT using FMOVI
            temp = self.generateTemp(Scope.InnerType.FLOAT)
            if temp is None:
                raise Exception("Failed to generate a valid temporary register for INT to FLOAT cast.")
            print(f"visitCastNode past the generateTemp for FLOAT")
            # co.code.append(IMovf(expr.temp, temp))
            convert_instr = IMovf(expr.temp, temp)  # Use IMovf for int to float
            co.code.append(convert_instr)
            co.temp = temp
            co.type = Scope.Type(Scope.InnerType.FLOAT)
            print(f"Cast INT to FLOAT: {convert_instr}")

        elif source_type == Scope.Type(Scope.InnerType.FLOAT) and target_type == Scope.Type(Scope.InnerType.INT):
            # Cast FLOAT -> INT using IMOVF
            temp = self.generateTemp(Scope.InnerType.INT)
            if temp is None:
                raise Exception("Failed to generate a valid temporary register for INT to FLOAT cast.")
            # co.code.append(FMovi(expr.temp, temp)) # MINE passes test 3 for FMovi
            convert_instr = FMovi(expr.temp, temp)  # Use FMovi for float to int
            co.code.append(convert_instr)
            co.temp = temp
            co.type = Scope.Type(Scope.InnerType.INT)
            print(f"Cast FLOAT to INT: {convert_instr}")

        else:
            # raise Exception(f"Unsupported cast from {source_type} to {target_type}")
            print(f"Unsupported cast from {source_type} to {target_type}")

        print(f"CastNode Output: Type={co.type}, Temp={co.temp}")

        return co

        # """
        # Generate code for a cast operation.
        # """
        # # Generate code for the expression being cast
        # expr_code = self.visit(node.expr)
        #
        # # Determine source and target types
        # source_type = expr_code.type
        # target_type = node.cast_type
        #
        # # If source and target types are the same, no casting is required
        # if source_type == target_type:
        #     return expr_code
        #
        # # Create a new CodeObject for the cast result
        # cast_code = CodeObject()
        # cast_code.type = target_type
        #
        # # Allocate a new register for the cast result
        # if target_type.isFloat():
        #     reg = f"{self.floatTempPrefix}{self.floatRegCount}"
        #     self.floatRegCount += 1
        # elif target_type.isInt():
        #     reg = f"{self.intTempPrefix}{self.intRegCount}"
        #     self.intRegCount += 1
        # else:
        #     raise Exception(f"Unsupported cast target type: {target_type}")
        #
        # cast_code.temp = reg
        #
        # # Generate the appropriate instruction
        # if source_type.isInt() and target_type.isFloat():
        #     cast_code.code.append(FMOVI(reg, expr_code.temp))  # Int to Float
        # elif source_type.isFloat() and target_type.isInt():
        #     cast_code.code.append(IMOVF(reg, expr_code.temp))  # Float to Int
        # else:
        #     raise Exception(f"Unsupported cast from {source_type} to {target_type}")
        #
        # return cast_code

#MINE for debug
    # def visitBinaryOpNode(self, node: BinaryOpNode):
    #     print(f"Processing BinaryOpNode: Op={node.getOp()}, Left={node.getLeft()}, Right={node.getRight()}")
    #     left = node.getLeft().accept(self)
    #     right = node.getRight().accept(self)
    #     print(f"BinaryOpNode Children: Left Temp={left.temp}, Right Temp={right.temp}")
    #     return self.postprocessBinaryOpNode(node, left, right)

    def lpostprocessBinaryOpNode(self, node: BinaryOpNode, left: CodeObject, right: CodeObject) -> CodeObject:

        co = CodeObject()
        # TODO FILL CODE FOR STEP 2

        # MINE
        #  working binary code passing test 0 and 1

        if left.lval:
            left = self.rvalify(left)
        co.code.extend(left.code)

        # Convert right operand to rvalue if needed
        if right.lval:
            right = self.rvalify(right)
        co.code.extend(right.code)

        # Determine the operation type
        optype = node.getOp()

        # Step 3: Determine the types of the operands, handling pointers
        if left.getType().type == Scope.InnerType.PTR:
            left_type = Scope.InnerType.INT
        else:
            left_type = left.getType().type

        if right.getType().type == Scope.InnerType.PTR:
            right_type = Scope.InnerType.INT
        else:
            right_type = right.getType().type


        # left_type = left.getType().type
        # right_type = right.getType().type

        # Handle matching types
        if left.type == right.type:
            # Step 4: ADD
            if node.getOp() == BinaryOpNode.OpType.ADD:
                if left_type == Scope.InnerType.FLOAT and right_type == Scope.InnerType.FLOAT:
                    dest = self.generateTemp(Scope.InnerType.FLOAT)
                    instr = FAdd(left.temp, right.temp, dest)
                elif left_type == Scope.InnerType.INT and right_type == Scope.InnerType.INT:
                    dest = self.generateTemp(Scope.InnerType.INT)
                    instr = Add(left.temp, right.temp, dest)
                else:
                    raise Exception("Unsupported operand types for ADD operation.")

            # Step 4: SUB
            elif node.getOp() == BinaryOpNode.OpType.SUB:
                if left_type == Scope.InnerType.FLOAT and right_type == Scope.InnerType.FLOAT:
                    dest = self.generateTemp(Scope.InnerType.FLOAT)
                    instr = FSub(left.temp, right.temp, dest)
                elif left_type == Scope.InnerType.INT and right_type == Scope.InnerType.INT:
                    dest = self.generateTemp(Scope.InnerType.INT)
                    instr = Sub(left.temp, right.temp, dest)
                else:
                    raise Exception("Unsupported operand types for SUB operation.")

            # Step 4: MUL and DIV
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

            # Step 4: Append the instruction to the code object
            co.code.append(instr)

            # # The result is in the destination temp register of the binary operation
            co.temp = instr.getDest()
            co.lval = False
            co.type = left.type  # Assume the type of the left operand for now


        # Handle mismatched types
        else:
            # Handle mismatched types (promote INT to FLOAT)
            if left_type == Scope.InnerType.INT and right_type == Scope.InnerType.FLOAT:
                # Promote left operand (INT) to FLOAT
                promoted_left_temp = self.generateTemp(Scope.InnerType.FLOAT)
                co.code.append(IMovf(left.temp, promoted_left_temp))
                left.temp = promoted_left_temp
                left_type = Scope.InnerType.FLOAT
            elif left_type == Scope.InnerType.FLOAT and right_type == Scope.InnerType.INT:
                # Promote right operand (INT) to FLOAT
                promoted_right_temp = self.generateTemp(Scope.InnerType.FLOAT)
                co.code.append(IMovf(right.temp, promoted_right_temp))
                right.temp = promoted_right_temp
                right_type = Scope.InnerType.FLOAT

            # Handle Pointer Arithmetic
            elif left_type == Scope.InnerType.PTR and right_type == Scope.InnerType.INT:
                # Pointer arithmetic: adding or subtracting an integer from a pointer is allowed.
                # We keep the pointer type as it is.
                pass

            elif right_type == Scope.InnerType.PTR and left_type == Scope.InnerType.INT:
                # Pointer arithmetic: adding or subtracting an integer from a pointer is allowed.
                # We keep the pointer type as it is.
                pass

                # If one operand is a pointer and the other is not an integer, or if both are pointers, raise an exception
            elif left_type == Scope.InnerType.PTR or right_type == Scope.InnerType.PTR:
                raise Exception(
                    "Unsupported pointer arithmetic involving two pointers or mixed types that are not supported.")

            else:
                # If types are still mismatched and cannot be resolved by promoting/demoting, raise an exception
                raise Exception("Unsupported operand type or pointer arithmetic")
            # Now that both types are FLOAT, generate the appropriate instruction
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

            # Update CodeObject properties
        co.lval = False
        print(f"BinaryOpNode Output Code: {co.code}")
        print(f"BinaryOpNode Final Temp: {co.temp}")
        print(f"BinaryOpNode Output: Left Temp={left.temp}, Right Temp={right.temp}, Type={co.type}")

        return co

    def postprocessBinaryOpNode(self, node: BinaryOpNode, left: CodeObject, right: CodeObject) -> CodeObject:
        co = CodeObject()

        # Step 1a: If left operand is an lval, convert it to rval
        if left.lval is True:
            left = self.rvalify(left)

        # Step 1: Add code from the left operand
        co.code.extend(left.code)

        # Step 2a: If right operand is an lval, convert it to rval
        if right.lval is True:
            right = self.rvalify(right)

        # Step 2: Add code from the right operand
        co.code.extend(right.code)

        # Determine the operation type
        optype = node.getOp()

        # Step 3: Determine the types of the operands, handling pointers
        if left.getType().type == Scope.InnerType.PTR:
            left_type = Scope.InnerType.INT  # Assume pointer arithmetic involves INT offsets
        else:
            left_type = left.getType().type

        if right.getType().type == Scope.InnerType.PTR:
            right_type = Scope.InnerType.INT  # Assume pointer arithmetic involves INT offsets
        else:
            right_type = right.getType().type

        # Handle type promotion if there is a mismatch
        if left_type == Scope.InnerType.INT and right_type == Scope.InnerType.FLOAT:
            # Promote left operand (INT) to FLOAT
            promoted_left_temp = self.generateTemp(Scope.InnerType.FLOAT)
            co.code.append(IMovf(left.temp, promoted_left_temp))
            left.temp = promoted_left_temp
            left_type = Scope.InnerType.FLOAT
        elif left_type == Scope.InnerType.FLOAT and right_type == Scope.InnerType.INT:
            # Promote right operand (INT) to FLOAT
            promoted_right_temp = self.generateTemp(Scope.InnerType.FLOAT)
            co.code.append(IMovf(right.temp, promoted_right_temp))
            right.temp = promoted_right_temp
            right_type = Scope.InnerType.FLOAT

        # Step 4: Generate the appropriate binary operation instruction
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

        # Step 5: Append the instruction to the code object
        co.code.append(instr)

        # Step 6: The result is in the destination temp register of the binary operation
        co.temp = instr.getDest()
        co.lval = False
        co.type = Scope.Type(left_type)  # Assume the type of the left operand for now

        return co

    #  Generate code for unary operations.
    #
    #  Step 0: create new code object
    #  Step 1: add code from child expression
    #  Step 1a: if child is an lval, add a load to get the data
    #  Step 2: generate instruction to perform unary operation (don't forget to generate right type of op)
    #
    #  Don't forget to update the temp and lval fields of the code object!
    #  	   Hint: where is the result stored? Is this data or an address?

    def postprocessUnaryOpNode(self, node: UnaryOpNode, expr: CodeObject) -> CodeObject:
        co = CodeObject()
        # TODO FILL IN CODE FOR STEP 2

        # Step 1: Convert the expression to an r-value if it's an l-value
        if expr.lval:
            expr = self.rvalify(expr)
            co.code.extend(expr.code)
        else:
            co.code.extend(expr.code)

            # Step 2: Generate the appropriate unary operation instruction
        if node.getOp() == UnaryOpNode.OpType.NEG:
            instr = Neg(expr.temp, self.generateTemp(expr.type.type))  # Generate Neg instruction
            co.code.append(instr)
            co.temp = instr.getDest()  # Assign the result temp

            # Step 3: Update the code object
        co.lval = False

        return co

        # Generate code for assignment statements
        #
        # Step 0: create new code object
        # Step 1a: if LHS is a variable, generate a load instruction to get the address into a register
        #          (see generateAddrFromVariable)
        # Step 1b: add code from LHS of assignment (make sure it results in an lval!)
        # Step 2: add code from RHS of assignment
        # Step 2a: if right child is an lval, add a load to get the data
        # Step 3: generate store (don't forget to generate the right type of store)
        #
        # Hint: it is going to be easiest to just generate a store with a 0 immediate
        # offset, and the complete store address in a register:
        #
        # sw rhs 0(lhs)

    def postprocessAssignNode(self, node: AssignNode, left: CodeObject, right: CodeObject) -> CodeObject:

        co = CodeObject()

        # TODO FILL IN CODE FOR STEP 2

        print(f"assign node enter")

        # Debugging: Log right-hand side before any processing
        print(f"AssignNode Input: Left Temp = {left.temp}, Left Type = {left.type}")
        print(f"AssignNode Input: Right Temp = {right.temp}, Right Type = {right.type}, Right Code = {right.code}")

        # Step 1: Handle left-hand side
        if left.isVar() and not left.getSTE().isLocal():
            left_instruction_list = self.generateAddrFromVariable(left)
            co.code.extend(left_instruction_list)
            left.temp = left_instruction_list[-1].getDest()  # Get the destination from the last instruction
        else:
            co.code.extend(left.code)

            # Step 2a: Convert right-hand side to r-value if needed
        if right.lval:
            right = self.rvalify(right)

        # Step 2: Handle right-hand side
        co.code.extend(right.code)




        # Step 2a: Convert right-hand side to r-value if needed
        if right.lval:
            if right.getSTE() is not None:  # Handle variables with STE
                if right.getType() is None:
                    raise Exception("Right-hand side has no type")
                if right.getType().type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
                    load_instr = Lw(self.generateTemp(right.getType().type), "fp", right.getSTE().addressToString())
                else:
                    load_instr = Flw(self.generateTemp(right.getType().type), "fp", right.getSTE().addressToString())
            else:  # Handle temporary variables
                if right.getType() is None:
                    raise Exception("Right-hand side has no type for temporary variable")
                if right.getType().type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
                    load_instr = Lw(self.generateTemp(right.getType().type), right.temp, "0")
                else:
                    load_instr = Flw(self.generateTemp(right.getType().type), right.temp, "0")

            co.code.append(load_instr)
            right.temp = load_instr.getDest()

        # # Handle type casting
        # left_type = left.getType().type
        # right_type = right.getType().type

        if left.type != right.type:  # Avoid redundant instructions
            print(f"Type mismatch detected: Left Type={left.type}, Right Type={right.type}")
            if left.type == Scope.Type(Scope.InnerType.INT) and right.type == Scope.Type(Scope.InnerType.FLOAT):
                print(f"Promoting FLOAT {right.temp} to INT for assignment")

                # Promote INT to FLOAT using FMOVI
                promoted_temp = self.generateTemp(Scope.InnerType.INT)
                # if promoted_temp is None:
                #     raise Exception("Failed to generate a valid temporary register for INT to FLOAT cast.")
                co.code.append(FMovi(right.temp, promoted_temp))
                right.temp = promoted_temp
                # right_type = Scope.InnerType.FLOAT
                # co.temp = promoted_temp  # Update co.temp to hold the new temp
                # co.type = Scope.Type(Scope.InnerType.INT)  # Set the correct type for the cast result
                print(f"Promotion complete: New Temp={right.temp}")


            elif left.type == Scope.Type(Scope.InnerType.FLOAT) and right.type == Scope.Type(Scope.InnerType.INT):
                print(f"Demoting INT {right.temp} to FLOAT for assignment")
                # Demote FLOAT to INT using IMOVF
                demoted_temp = self.generateTemp(Scope.InnerType.FLOAT)
                # if demoted_temp is None:
                #     raise Exception("Failed to generate a valid temporary register for INT to FLOAT cast.")
                co.code.append(IMovf(right.temp, demoted_temp))
                right.temp = demoted_temp
                # right_type = Scope.InnerType.INT
                # co.temp = demoted_temp  # Update co.temp to hold the new temp
                # co.type = Scope.Type(Scope.InnerType.FLOAT)  # Set the correct type for the cast result
                print(f"Demotion complete: New Temp={right.temp}")

        # # Step 3: Type Mismatch Handling
        # # Step 3: Type Mismatch Handling
        # typeconv = False
        # typeconvtemp = None
        # convertcode = None  # Ensure `convertcode` is always initialized
        #
        # if left.type != right.type:
        #         if left.type == Scope.Type(Scope.InnerType.INT) and right.type == Scope.Type(Scope.InnerType.FLOAT):
        #             # Demote FLOAT to INT
        #             typeconvtemp = self.generateTemp(Scope.InnerType.INT)
        #             convertcode = FMovi(right.temp, typeconvtemp)  # Use FMovi for FLOAT → INT
        #             typeconv = True
        #
        #         elif left.type == Scope.Type(Scope.InnerType.FLOAT) and right.type == Scope.Type(Scope.InnerType.INT):
        #             # Promote INT to FLOAT
        #             typeconvtemp = self.generateTemp(Scope.InnerType.FLOAT)
        #             convertcode = IMovf(right.temp, typeconvtemp)  # Use IMovf for INT → FLOAT
        #             typeconv = True
        #
        #         if typeconv:
        #             co.code.append(convertcode)
        #             right.temp = typeconvtemp
#######################################

        # if left_type != right_type:  # Avoid redundant instructions
        #     if left_type == Scope.InnerType.FLOAT and right_type == Scope.InnerType.INT:
        #
        #
        #         # Promote INT to FLOAT using FMOVI
        #         promoted_temp = self.generateTemp(Scope.InnerType.FLOAT)
        #
        #         debug_comment = f"; Promoting INT {right.temp} to FLOAT {promoted_temp}"
        #         co.code.append(debug_comment)  # Append debug comment as a "fake" instruction
        #         print(debug_comment)
        #
        #         co.code.append(IMovf(right.temp, promoted_temp))
        #         right.temp = promoted_temp
        #         # right_type = Scope.InnerType.FLOAT
        #
        #     elif left_type == Scope.InnerType.INT and right_type == Scope.InnerType.FLOAT:
        #         # Demote FLOAT to INT using IMOVF
        #         demoted_temp = self.generateTemp(Scope.InnerType.INT)
        #
        #         debug_comment = f"; Demoting FLOAT {right.temp} to INT {demoted_temp}"
        #         co.code.append(debug_comment)  # Append debug comment as a "fake" instruction
        #         print(debug_comment)
        #
        #         co.code.append(FMovi(right.temp, demoted_temp))
        #         right.temp = demoted_temp
        #         # right_type = Scope.InnerType.INT


        # Debugging Step 3: Check final CodeObject
        # Debugging Step 3: Check final CodeObject
        print(f"AssignNode Debug: Final CodeObject before store: Temp={co.temp}, Type={co.type}, Code={co.code}")

        # Step 3: Generate the store instruction for the left-hand side
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


        # co.temp = right.temp  # Update the temporary register
        # co.type = right.type  # Update the type
            # Debugging: Log after processing
        print(f"AssignNode Output: Left Temp = {left.temp}, Right Temp = {right.temp}, Code = {co.code}")
        co.temp = right.temp
        co.type = right.type
        return co

    def debugpostprocessBinaryOpNode(self, node, left, right):
        co = CodeObject()
        print(f"BinaryOpNode Input: Left Temp={left.temp}, Right Temp={right.temp}")

        # Convert left operand to rvalue if needed
        if left.lval:
            left = self.rvalify(left)
        if left.temp is None:
            raise Exception("Left operand in BinaryOpNode did not produce a valid temp.")
        co.code.extend(left.code)

        # Convert right operand to rvalue if needed
        if right.lval:
            right = self.rvalify(right)
        if right.temp is None:
            raise Exception("Right operand in BinaryOpNode did not produce a valid temp.")
        co.code.extend(right.code)

        # Ensure that we have valid types for operation
        if left.type is None or right.type is None:
            raise Exception("Left or right operand type is None.")

        # Debug after rvalify
        print(f"BinaryOpNode After Rvalify: Left Temp={left.temp}, Right Temp={right.temp}")

        # Determine the operation type and generate the appropriate instruction
        optype = node.getOp()
        result_temp = self.generateTemp(
            Scope.InnerType.FLOAT if left.type == Scope.InnerType.FLOAT or right.type == Scope.InnerType.FLOAT else Scope.InnerType.INT)

        if result_temp is None:
            raise Exception("Failed to generate a result temp for BinaryOpNode.")

        # Example for ADD operation (similar logic for others)
        if optype == BinaryOpNode.OpType.ADD:
            if left.type == Scope.InnerType.FLOAT or right.type == Scope.InnerType.FLOAT:
                instr = FAdd(left.temp, right.temp, result_temp)
            else:
                instr = Add(left.temp, right.temp, result_temp)
        else:
            raise Exception(f"Unsupported binary operation type: {optype}")

        # Append the generated instruction to code
        co.code.append(instr)
        co.temp = instr.getDest()
        co.lval = False
        co.type = Scope.Type(
            Scope.InnerType.FLOAT if left.type == Scope.InnerType.FLOAT or right.type == Scope.InnerType.FLOAT else Scope.InnerType.INT)

        # Debug output
        print(f"BinaryOpNode Final Temp: {co.temp}, Final Code: {co.code}")

        return co

    def debugpostprocessCastNode(self, node, expr):
        if expr.temp is None:
            print("CastNode found expr without a valid temp. Forcing temp generation.")
            expr.temp = self.generateTemp(expr.getType().type)

        # Proceed with the rest of the cast logic
        return expr

    def debugpostprocessAssignNode(self, node, left, right):
        co = CodeObject()
        print(
            f"AssignNode Input: Left Temp={left.temp}, Left Type={left.type}, Right Temp={right.temp}, Right Type={right.type}")

        # Generate a temp for left if needed
        if left.temp is None:
            if left.type is None:
                raise Exception("Left operand type is None, cannot generate temp.")
            if not isinstance(left.type, Scope.Type):
                raise Exception(f"Unexpected type for left operand: {left.type}. Expected Scope.Type.")
            left.temp = self.generateTemp(left.type.type)

        # Add code for the right-hand side
        co.code.extend(right.code)

        # Type Handling (Promote/Demote)
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

        # Store instruction for left-hand side
        if left.getSTE() is not None and left.getSTE().isLocal():
            instr = Sw(right.temp, "fp", left.getSTE().addressToString())
        else:
            instr = Sw(right.temp, left.temp, "0")
        co.code.append(instr)

        # Update CodeObject
        co.temp = right.temp
        co.type = right.type

        print(f"AssignNode Output Code: {co.code}")

        return co

    # Add together all the lists of instructions generated by the children

    def postprocessStatementListNode(self, node: StatementListNode, statements: list) -> CodeObject:
        co = CodeObject()

        for subcode in statements:
            co.code.extend(subcode.code)

        co.type = None
        return co

        # Generate code for read
        #
        # Step 0: create new code object
        # Step 1: add code from VarNode (make sure it's an lval)
        # Step 2: generate GetI instruction, storing into temp
        # Step 3: generate store, to store temp in variable

    def postprocessReadNode(self, node: ReadNode, var: CodeObject) -> CodeObject:
        co = CodeObject()
        assert (var.getSTE() is not None)

        il = InstructionList()

        typ = node.getType()

        if typ.type == Scope.InnerType.INT:
            # Code to generate if INT:
            #	geti tmp
            # if var is global: la tmp', <var>; sw tmp 0(tmp')
            # if var is local: sw tmp offset(fp)
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
            # Code to generate if FLOAT:
            #	getf tmp
            # if var is global: la tmp', <var>; fsw tmp 0(tmp')
            # if var is local: fsw tmp offset(fp)
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

        co.lval = False  # doesn't matter
        co.temp = None  # set to None to trigger errors
        co.type = None  # set to None to trigger errors

        return co

    # Generate code for print
    #
    # Step 0: create new code object
    #
    # If printing a string:
    # Step 1: add code from expression to be printed (make sure it's an lval)
    # Step 2: generate a PutS instruction printing the result of the expression
    #
    # If printing an integer:
    # Step 1: add code from the expression to be printed
    # Step 1a: if it's an lval, generate a load to get the data
    # Step 2: Generate PutI that prints the temporary holding the expression

    def postprocessWriteNode(self, node: WriteNode, expr: CodeObject) -> CodeObject:
        co = CodeObject()
        # generating code for write(expr)

        # for strings, we expect a variable
        if node.getWriteExpr().getType().type == Scope.InnerType.STRING:
            # Step 1:
            assert (expr.getSTE() is not None)

            # print(f"; generating code to print {expr.getSTE()}")

            # Get the address of the variable
            addrCo = self.generateAddrFromVariable(expr)
            co.code.extend(addrCo)

            # Step 2:
            write = PutS(addrCo.getLast().getDest())
            co.code.append(write)
        else:
            # Step 1a:
            # if expr is an lval, load from it
            if expr.lval is True:
                expr = self.rvalify(expr)

            # Step 1:
            co.code.extend(expr.code)

            # Step 2:
            # if type of writenode is int, use puti, if float, use putf
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

        co.lval = False  # doesn't matter
        co.temp = None  # set to None to trigger errors
        co.type = None  # set to None to trigger errors
        return co

    #  Generating an instruction sequence for a conditional expression
    #
    #  Implement this however you like. One suggestion:
    #
    #  Create the code for the left and right side of the conditional, but defer
    #  generating the branch until you process IfStatementNode or WhileNode (since you
    #  do not know the labels yet). Modify CodeObject so you can save the necessary
    #  information to generate the branch instruction in IfStatementNode or WhileNode
    #
    #  Alternate idea 1:
    #
    #  Don't do anything as part of CodeGenerator. Create a new visitor class
    #  that you invoke *within* your processing of IfStatementNode or WhileNode
    #
    #  Alternate idea 2:
    #
    #  Create the branch instruction in this function, then tweak it as necessary in
    #  IfStatementNode or WhileNode
    #
    #  Hint: you may need to preserve extra information in the returned CodeObject to
    #  make sure you know the type of branch code to generate (int vs float)

    def postprocessCondNode(self, node: CondNode, left: CodeObject, right: CodeObject) -> CodeObject:
        co = CodeObject()
        # TODO FILL IN CODE FROM STEP 3

        # Convert left and right operands to rvals if necessary
        if left.lval:
            left = self.rvalify(left)
        co.code.extend(left.code)

        if right.lval:
            right = self.rvalify(right)
        co.code.extend(right.code)

        # Set ltemp and rtemp to the temporary values from left and right
        co.ltemp = left.temp  # Assign the left temp
        co.rtemp = right.temp  # Assign the right temp

        # Step 3: Determine the branch operation and data type
        if left.getType().type == Scope.InnerType.INT and right.getType().type == Scope.InnerType.INT:
            co.type = Scope.Type(Scope.InnerType.INT)

        elif left.type == Scope.Type(Scope.InnerType.FLOAT) and right.type == Scope.Type(Scope.InnerType.FLOAT):
            co.type = Scope.Type(Scope.InnerType.FLOAT)

        else:
            raise ValueError(f"Incompatible operand types for CondNode: {left.type} and {right.type}")

        # Set cond_type based on the operation
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

        co.lval = False  # This is not an l-value (not assignable)
        co.temp = None
        co.conop = co.cond_type

        return co

    # Code generation for IfStatement
    # Step 0: Create code object
    #
    # Step 1: generate labels
    #
    # Step 2: add code from conditional expression
    #
    # Step 3: create branch statement (if not created as part of step 2)
    # 			don't forget to generate correct branch based on type
    #
    # Step 4: generate code
    # 		<cond code>
    #		<flipped branch> elseLabel
    #		<then code>
    #		j outLabel
    #		elseLabel:
    #		<else code>
    #		outLabel:
    #
    # Step 5 insert code into code object in appropriate order.

    def postprocessIfStatementNode(self, node: IfStatementNode, cond: CodeObject, tlist: CodeObject,
                                   elist: CodeObject) -> CodeObject:
        co = CodeObject()
        # TODO FILL IN CODE FROM STEP 3

        # Generate labels
        else_present = elist and elist.code
        else_label = self.generateElseLabel() if else_present else self.generateOutLabel()
        out_label = self.generateOutLabel()
        temp_float = self.generateTemp(Scope.InnerType.INT)

        # Add condition code
        co.code.extend(cond.code)

        comp = None
        # Handle integer comparisons
        if cond.type.type == Scope.InnerType.INT:
            op = cond.cond_type  # Assuming 'cond_type' stores the operator from cond node
            # print(f"Handling INT comparison, op: {op}")
            if op == "==":
                # print("Setting comp to Bne for ==")
                comp = Bne(cond.ltemp, cond.rtemp, else_label)
            elif op == "!=":
                # print("Setting comp to Beq for !=")
                comp = Beq(cond.ltemp, cond.rtemp, else_label)
            elif op == "<":
                # print("Setting comp to Blt for <")
                comp = Bge(cond.ltemp, cond.rtemp, else_label)
            elif op == ">":
                # print("Setting comp to Bgt for >")
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

        # Add the "then" block code
        co.code.extend(tlist.code) \
 \
        # Unconditional jump to the "out" label
        co.code.append(J(out_label))

        # Add the "else" block (if present)
        co.code.append(Label(else_label))
        if elist:
            co.code.extend(elist.code)

        # Mark the end of the if-else block with the "out" label
        co.code.append(Label(out_label))

        return co

    # Code generation for While statement
    # Step 0: Create code object
    #
    # Step 1: generate labels
    #
    # Step 2: add code from conditional expression
    #
    # Step 3: create branch statement (if not created as part of step 2)
    # 			don't forget to generate correct branch based on type
    #
    # Step 4: generate code
    # 		loopLabel:
    #		<cond code>
    #		<flipped branch> outLabel
    #		<body code>
    #		j loopLabel
    #		outLabel:
    #
    # Step 5 insert code into code object in appropriate order.

    def postprocessWhileNode(self, node: WhileNode, cond: CodeObject, wlist:
    CodeObject) -> CodeObject:
        co = CodeObject()
        # TODO FILL IN CODE FROM STEP 3

        # Step 1: Generate labels for loop start and exit
        loop_label = self.generateLoopLabel()
        exit_label = self.generateOutLabel()

        # Step 2: Add the loop start label
        co.code.append(Label(loop_label))

        # Step 3: Add the condition evaluation code
        co.code.extend(cond.code)

        branch_inst = None

        if cond.type.type == Scope.InnerType.INT:
            op = cond.cond_type  # Use condition operator from cond node
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

        # Step 5: Add the branch instruction
        co.code.append(branch_inst)

        # Step 6: Add the while body (loop body) code
        co.code.extend(wlist.code)

        # Step 7: Add jump back to the loop start
        co.code.append(J(loop_label))

        # Step 8: Add the exit label to exit the loop
        co.code.append(Label(exit_label))

        return co

    # FILL IN FOR STEP 4
    #
    # Generating code for returns
    #
    # Step 0: Generate new code object
    #
    # Step 1: Add retExpr code to code object (rvalify if necessary)
    #
    # Step 2: Store result of retExpr in appropriate place on stack (fp + 8)
    #
    # Step 3: Jump to out label (use @link{generateFunctionOutLabel()})

    def postprocessReturnNode(self, node: ReturnNode, retExpr: CodeObject) -> CodeObject:
        co = CodeObject()

        # TODO FILL IN
        # Step 1: Check if retExpr is None
        if retExpr is None:
            return co

        # Step 1: Add retExpr code to code object (rvalify if necessary)
        if retExpr.lval:
            retExpr = self.rvalify(retExpr)
        co.code.extend(retExpr.code)

        # Step 2: Store result of retExpr in appropriate place on stack (fp + 8)
        if retExpr.getType().type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
            i = Sw(retExpr.temp, "fp", "8")  # Store int return value at fp + 8
            co.code.append(i)
        elif retExpr.getType().type == Scope.InnerType.FLOAT:
            i = Fsw(retExpr.temp, "fp", "8")  # Store float return value at fp + 8
            co.code.append(i)

        # Step 3: Jump to out label
        i = J(self.generateFunctionOutLabel())
        co.code.append(i)

        return co

    def preprocessFunctionNode(self, node: FunctionNode):
        # Generate function label information, used for other labels inside function

        self.currFunc = node.getFuncName()

        # reset register counts; each function uses new registers!
        self.intRegCount = 0
        self.floatRegCount = 0

    # FILL IN FOR STEP 4
    #
    # Generate code for functions
    #
    # Step 1: add the label for the beginning of the function
    #
    # Step 2: manage frame  pointer
    # 			a. Save old frame pointer
    # 			b. Move frame pointer to point to base of activation record (current sp)
    # 			c. Update stack pointer
    #
    # Step 3: allocate new stack frame (use scope infromation from FunctionNode)
    #
    # Step 4: save registers on stack (Can inspect intRegCount and floatRegCount to know what to save)
    #
    # Step 5: add the code from the function body
    #
    # Step 6: add post-processing code:
    # 			a. Label for `return` statements inside function body to jump to
    # 			b. Restore registers
    # 			c. Deallocate stack frame (set stack pointer to frame pointer)
    # 			d. Reset fp to old location
    # 			e. Return from function

    def postprocessFunctionNode(self, node: FunctionNode, body: CodeObject) -> CodeObject:
        co = CodeObject()

        # TODO FILL IN

        # Step 1: Add the label for the beginning of the function
        i = Label("func_" + node.getFuncName())
        co.code.append(i)

        # Step 2: Manage frame pointer
        # a. Save old frame pointer
        i = Sw("fp", "sp", "0")  # Store old frame pointer at current sp
        co.code.append(i)

        # b. Move frame pointer to point to base of activation record (current sp)
        i = Mv("sp", "fp")  # Move sp to fp
        co.code.append(i)

        # c. Update stack pointer
        i = Addi("sp", "-4", "sp")  # Adjust stack pointer for the saved frame pointer
        co.code.append(i)

        # Step 3: Allocate new stack frame (use scope information from FunctionNode)
        i = Addi("sp", str(node.getScope().getNumLocals() * -4), "sp")  # Allocate space for local variables
        co.code.append(i)

        # Step 4: Save registers on stack
        int_count = self.getIntRegCount()  # Number of int registers
        float_count = self.getFloatRegCount()  # Number of float registers

        # Save int registers
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

        # Step 6b: Restore registers
        # Restore float registers (in reverse order)
        # for val in range(1, float_count + 1):
        for val in range(1, float_count + 1):
            # co.code.extend(self.popRegister(f"f{float_count + 1 - val}", Scope.Type.FLOAT).code)
            co.code.extend(self.popRegister(f"f{float_count + 1 - val}", Scope.Type(Scope.InnerType.FLOAT)).code)

        # Restore int registers (in reverse order)
        for val in range(1, int_count + 1):
            # co.code.extend(self.popRegister(f"t{int_count + 1 - val}", Scope.Type.INT).code)
            co.code.extend(self.popRegister(f"t{int_count + 1 - val}", Scope.Type(Scope.InnerType.INT)).code)

        # Step 6c: Deallocate stack frame (set stack pointer to frame pointer)
        i = Mv("fp", "sp")  # Move fp back to sp
        co.code.append(i)

        # Step 6d: Reset frame pointer to the old location
        i = Lw("fp", "fp", "0")  # Load old frame pointer back
        co.code.append(i)

        # Step 6e: Return from function
        i = Ret()  # Return instruction
        co.code.append(i)

        return co

    # Generate code for the list of functions. This is the "top level" code generation function
    #
    # Step 1: Set fp to point to sp
    #
    # Step 2: Insert a JR to main
    #
    # Step 3: Insert a HALT
    #
    # Step 4: Include all the code of the functions

    def postprocessFunctionListNode(self, node: FunctionListNode, functions: List[CodeObject]) -> CodeObject:
        co = CodeObject()

        co.code.append(Mv("sp", "fp"))
        co.code.append(Jr(self.generateFunctionLabel("main")))
        co.code.append(Halt())
        co.code.append(Blank())

        # Add code for each of the functions
        for c in functions:
            co.code.extend(c.code)
            co.code.append(Blank())

        return co

    # FILL IN FOR STEP 4
    #
    # Generate code for a call expression
    #
    # Step 1: For each argument:
    #
    # 	Step 1a: insert code of argument (don't forget to rvalify!)
    #
    # 	Step 1b: push result of argument onto stack
    #
    # Step 2: alloate space for return value
    #
    # Step 3: push current return address onto stack
    #
    # Step 4: jump to function
    #
    # Step 5: pop return address back from stack
    #
    # Step 6: pop return value into fresh temporary (destination of call expression)
    #
    # Step 7: remove arguments from stack (move sp)
    #
    # FOR STEP 6: Add special handling for malloc and free
    #
    # FOR STEP 6: Make sure to handle VOID functions properly
    def postprocessCallNode(self, node: CallNode, args: List[CodeObject]) -> CodeObject:
        co = CodeObject()
        # func_name = node.getFuncName()

        # TODO FILL IN

        # Step 1: For each argument
        for codeobj in args:

            if codeobj.lval:
                codeobj = self.rvalify(codeobj)
            co.code.extend(codeobj.code)

            # Step 1b: Push result of argument onto stack
            co.code.extend(self.pushRegister(codeobj.temp, codeobj.getType()).code)

        # Step 2: Allocate space for return value
        i = Addi("sp", "-4", "sp")
        co.code.append(i)

        # Step 3: Push current return address onto stack
        co.code.extend(self.pushRegister("ra", Scope.Type(Scope.InnerType.INT)).code)

        # Step 4: Jump to function
        func_name = node.getFuncName()
        i = Jr("func_" + func_name)
        co.code.append(i)

        # Step 5: Pop return address back from stack
        co.code.extend(self.popRegister("ra", Scope.Type(Scope.InnerType.INT)).code)

        return_type = node.getType().type

        if return_type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
            codeObj = self.popRegister(self.generateTemp(Scope.InnerType.INT), Scope.Type(Scope.InnerType.INT))
            co.code.extend(codeObj.code)
            co.temp = codeObj.code[-1].getDest()  # Get the destination of the last instruction
        elif return_type == Scope.InnerType.FLOAT:
            codeObj = self.popRegister(self.generateTemp(Scope.InnerType.FLOAT), Scope.Type(Scope.InnerType.FLOAT))
            co.code.extend(codeObj.code)
            co.temp = codeObj.code[-1].getDest()
        elif return_type == Scope.InnerType.VOID:
            i = Addi("sp", "4", "sp")  # Adjust stack pointer
            co.code.append(i)

        # Step 7: Remove arguments from stack (move sp)
        i = Addi("sp", str(len(args) * 4), "sp")
        co.code.append(i)

        co.type = node.getType()

        return co

    def pushRegister(self, register: str, reg_type: Scope.Type) -> CodeObject:
        co = CodeObject()

        # Determine the inner type of the register
        if reg_type.type == Scope.InnerType.PTR:
            # co_type = reg_type.getWrappedType().type
            co_type = Scope.InnerType.INT  # Treat PTR as INT for SW instruction
        else:
            co_type = reg_type.type

        # Generate the appropriate instruction based on the type
        if co_type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
            instr = Sw(register, "sp", "0")  # Store word for INT or PTR
            co.code.append(instr)
        elif co_type == Scope.InnerType.FLOAT:
            instr = Fsw(register, "sp", "0")  # Store float word for FLOAT
            co.code.append(instr)

        # Decrement stack pointer
        i = Addi("sp", "-4", "sp")
        co.code.append(i)

        return co

    def popRegister(self, register: str, reg_type: Scope.Type) -> CodeObject:
        co = CodeObject()

        # Increment stack pointer
        i = Addi("sp", "4", "sp")
        co.code.append(i)

        if reg_type.type == Scope.InnerType.INT:
            i = Lw(register, "sp", "0")
            co.code.append(i)
            co.temp = i.getDest()
        # elif reg_type == Scope.Type.FLOAT:
        elif reg_type.type == Scope.InnerType.FLOAT:
            i = Flw(register, "sp", "0")
            co.code.append(i)
            co.temp = i.getDest()

        return co

    # Generate code for * (expr)
    #
    # Goal: convert the r-val coming from expr (a computed address) into an l-val (an address that can be loaded/stored)
    #
    # Step 0: Create new code object
    #
    # Step 1: Rvalify expr if needed
    #
    # Step 2: Copy code from expr (including any rvalification) into new code object
    #
    # Step 3: New code object has same temporary as old code, but now is marked as an l-val
    #
    # Step 4: New code object has an "unwrapped" type: if type of expr is * T, type of temporary is T. Can get this from node
    def postprocessPtrDerefNode(self, node: PtrDerefNode, expr: CodeObject) -> CodeObject:

        co = CodeObject()

        if expr.lval:  # This means if expr is an r-val
            expr = self.rvalify(expr)

        co.code.extend(expr.code)  # Copy code

        co.temp = expr.temp  # Use same temporary
        co.lval = True  # Mark as lval
        co.type = node.getType()

        return co

        # print(f"Processing PtrDerefNode, expr type: {expr.type}")
        # print(f"Initial expr type: {expr.type}, temp: {expr.temp}, lval: {expr.lval}")
        #
        # co = CodeObject()
        # # TODO FILL IN FOR STEP 6
        #
        #
        # # Step 1: Rvalify expr if needed (only if expr is not already an l-val)
        # if expr.lval:  # This means if expr is an r-val
        #     expr = self.rvalify(expr)
        # #     print(f"Rvalified expr: {expr}, temp: {expr.temp}, type: {expr.type}")
        # #     print(f"After rvalify in PtrDerefNode: temp={expr.temp}, type={expr.type}, lval={expr.lval}")
        # #
        # # if expr.temp is None:
        # #     print(f"PtrDerefNode Error: temp is None for expr={expr}")
        #
        # # Step 2: Copy code from expr into the new code object
        # co.code.extend(expr.code)
        #
        # # Step 3: Use the same temporary but mark as lval
        # co.temp = expr.temp
        #
        # co.lval = True
        # #
        # co.type = node.getType()
        #
        # # # # Step 4: Set type to "unwrapped" type
        # # co.type = node.getType()  # Assuming `node.getType()` returns the dereferenced type (e.g., T from *T)
        # #
        # # # Step 4: Set type to "unwrapped" type (retrieve the base type from *T)
        # # co.type = expr.type.getWrappedType() if expr.type else None  # Safely unwrap if expr has a type
        # # co.type = expr.type.getWrappedType()  # Safely unwrap if expr has a type
        # # co.ste = expr.getSTE()  # This assumes the underlying `expr` has an `STE`, which may represent `ptr`
        #
        # # # print(f"Dereferencing type: {expr.type}, Unwrapped type: {co.type}")
        # # # print("Exiting postprocessPtrDerefNode with co:", co)
        # # print(f"Processed PtrDerefNode: type={co.type}, temp={co.temp}, lval={co.lval}")
        # print(f"Processed PtrDerefNode: type={co.type}, temp={co.temp}, lval={co.lval}")
        # return co

    # Generate code for a & (expr)
    #
    # Goal: convert the lval coming from expr (an address) to an r-val (a piece of data that can be used)
    #
    # Step 0: Create new code object
    #
    # Step 1: If lval is a variable, generate code to put address into a register (e.g., generateAddressFromVar)
    #			Otherwise just copy code from other code object
    #
    # Step 2: New code object has same temporary as existing code, but is an r-val
    #
    # Step 3: New code object has a "wrapped" type. If type of expr is T, type of temporary is *T. Can get this from node
    def postprocessAddrOfNode(self, node: AddrOfNode, expr: CodeObject) -> CodeObject:

        co = CodeObject()
        # TODO FILL IN CODE FOR STEP 6

        # Step 1: If expr is a variable, get its address
        if expr.isVar():
            addr_instructions = self.generateAddrFromVariable(expr)
            co.code.extend(addr_instructions)
            expr.temp = addr_instructions.getLast().getDest()

        # Add code from expression
        co.code.extend(expr.code)

        # Step 2: Mark as r-val
        co.temp = expr.temp

        co.lval = False

        # Step 3: set the type
        co.type = node.getType()

        return co

    # Generate code for malloc
    #
    # Step 0: Create new code object
    #
    # Step 1: Add code from expression (rvalify if needed)
    #
    # Step 2: Create new MALLOC instruction
    #
    # Step 3: Set code object type to INFER
    def postprocessMallocNode(self, node: MallocNode, expr: CodeObject) -> CodeObject:
        co = CodeObject()
        # TODO FILL IN CODE FOR STEP 6

        # Step 1: Rvalify and add code from expr
        # if expr.lval is False:
        if expr.lval:
            expr = self.rvalify(expr)
        co.code.extend(expr.code)
        # print(f"MallocNode rvalify check: expr type is {expr.type}")

        # Step 2: Create a MALLOC instruction

        dest = self.generateTemp(expr.getType().type)  # match type with expression
        malloc_instr = Malloc(expr.temp, dest)  # allocate memory
        co.code.append(malloc_instr)

        # Step 3: Set code object to infer type from `node`
        co.temp = dest
        co.type = Scope.Type(Scope.InnerType.PTR)
        co.lval = False  # Result of malloc is an r-value

        return co

    #  Generate code for free
    #
    #  Step 0: Create new code object
    #
    #  Step 1: Add code from expression (rvalify if needed)
    #
    #  Step 2: Create new FREE instruction
    def postprocessFreeNode(self, node: FreeNode, expr: CodeObject) -> CodeObject:

        co = CodeObject()
        # TODO FILL IN CODE FOR STEP 6

        # Step 1: Rvalify and add code from expr
        if expr.lval:
            expr = self.rvalify(expr)
        co.code.extend(expr.code)

        # Step 2: Generate the Free instruction
        free_instr = Free(expr.temp)
        co.code.append(free_instr)

        return co

    # Generate a fresh temporary
    #
    # @return new temporary register name

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

        # Take a code object that results in an lval, and create a new code
        # object that adds a load to generate the rval.
        #
        # Step 0: Create new code object
        #
        # Step 1: Add all the lco code to the new code object
        # 		   (If lco is just a variable, create a new code object that
        #          stores the address of variable in a code object; see
        #          generateAddrFromVariable)
        #
        # Step 2: Generate a load to load from lco's temp into a new temporary
        # 		   Hint: it'll be easiest to generate a load with no offset:
        # 				lw newtemp 0(oldtemp)
        #         Don't forget to generate the right kind of load based on the type
        #         stored in the address
        #
        # Don't forget to update the temp and lval fields of the code object!
        # 		   Hint: where is the result stored? Is this data or an address?
        #
        # @param lco The code object resulting in an address
        # @return A code object with all the code of <code>lco</code> followed by a load
        #         to generate an rval

    def rvalify(self, lco: CodeObject) -> CodeObject:

        # # TODO FILL IN CODE FROM STEP 2

        assert (lco.lval is True)

        co = CodeObject()

        # Determine if the SymbolTableEntry is null
        ste_is_null = lco.getSTE() is None

        # Step 1: Add code from lco to co
        co.code.extend(lco.code)

        # Get the InnerType of the CodeObject
        co_type = lco.getType().type

        # Step 2: Generate the appropriate load instruction
        if ste_is_null:
            # If no SymbolTableEntry, assume it is a temporary
            if co_type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
                load_instr = Lw(self.generateTemp(co_type), lco.temp, "0")
            else:
                load_instr = Flw(self.generateTemp(co_type), lco.temp, "0")
        else:
            # If SymbolTableEntry exists, use its address
            symbol = lco.getSTE()
            address = symbol.addressToString()

            if co_type in [Scope.InnerType.INT, Scope.InnerType.PTR]:
                load_instr = Lw(self.generateTemp(co_type), "fp", address)
            else:
                load_instr = Flw(self.generateTemp(co_type), "fp", address)

        # Step 3: Add the load instruction to the code
        co.code.append(load_instr)

        # Step 4: Update the CodeObject's temporary and type information
        co.temp = load_instr.getDest()
        co.lval = False
        co.type = lco.getType()

        return co

    # Generate an instruction sequence that holds the address of the variable in a code object
    #
    # If it's a global variable, just get the address from the symbol table
    #
    # If it's a local variable, compute the address relative to the frame pointer (fp)
    #
    # @param lco The code object holding a variable
    # @return a list of instructions that puts the address of the variable in a register

    def generateAddrFromVariable(self, lco: CodeObject) -> InstructionList:

        il = InstructionList()

        # Step 1:
        symbol = lco.getSTE()
        address = symbol.addressToString()

        # Step 2:
        if symbol.isLocal():
            # If local, address is offset
            # need to load fp + offset
            # addi tmp' fp offset
            compAddr = Addi("fp", address, self.generateTemp(Scope.InnerType.INT))
        else:
            # If global, address in symbol table is the right location
            # la tmp' addr // Register type needs to be an int
            compAddr = La(self.generateTemp(Scope.InnerType.INT), address)
        il.append(compAddr)  # add instruction

        return il
