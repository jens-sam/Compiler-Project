# Custom Compiler Backend with RISC-V Assembly Code Generation

This repository contains a portfolio snapshot of a Python-based compiler backend developed as part of graduate-level computer engineering coursework at Purdue University.

The project focused on backend code generation: translating typed abstract syntax tree (AST) representations into RISC-V-style assembly instruction sequences using an AST visitor-based framework.

## Repository Note

This repository is intended for viewing and portfolio demonstration only.

The full course compiler framework included additional parser, AST, symbol table, instruction, testing, and runtime files that are not included in this public repository. As a result, this repository is not intended to run as a standalone compiler. The included files highlight the backend implementation work, code-generation structure, and project design.

## Project Overview

The compiler backend operates after parsing and semantic analysis. It uses typed AST nodes and symbol table information to generate low-level instruction sequences for expressions, statements, control flow, functions, and memory operations.

The main implementation centers on the `CodeGenerator` class, which walks the AST and emits RISC-V-style assembly instructions. Supporting classes such as `CodeObject` and `InstructionList` manage generated code, temporary registers, type information, conditional metadata, and l-value/r-value state.

## Included Files

- `CodeGenerator.py`  
  Main compiler backend implementation. Handles AST visitor postprocessing and emits RISC-V-style instruction sequences.

- `CodeObject.py`  
  Stores generated instructions, temporary register names, type information, l-value/r-value state, and conditional-expression metadata.

- `InstructionList.py`  
  Manages ordered instruction output and formats generated instruction sequences into readable assembly-style text.

- `__init__.py`  
  Package initialization file for the backend module.

## Implemented Backend Features

- Python-based compiler backend structure
- AST visitor-based code generation
- RISC-V-style assembly instruction generation
- Integer and floating-point literal handling
- Unary and binary arithmetic operations
- Type casting between integer and floating-point values
- Assignment handling
- L-value and r-value conversion
- Symbol table-based variable access
- Local variable addressing through the frame pointer
- Global variable address generation
- Conditional expressions
- If/else control flow
- While-loop generation
- Branch-label generation
- Function definition code generation
- Function call handling
- Return-value handling
- Stack-frame setup and teardown
- Register save/restore behavior
- Argument passing through the stack
- Pointer dereferencing
- Address-of operations
- Dynamic memory allocation support
- Memory deallocation support

## Technical Focus

This project demonstrates backend compiler implementation in Python, including how high-level programming constructs are lowered into assembly-style instruction sequences.

The implementation includes logic for:

- temporary register generation,
- integer and floating-point instruction paths,
- load/store instruction generation,
- control-flow branching,
- stack-frame management,
- function prologue and epilogue generation,
- return address preservation,
- type-specific instruction emission,
- pointer and memory operation handling.

## Skills Demonstrated

- Python
- Compiler backend development
- RISC-V-style assembly generation
- AST traversal
- Object-oriented programming
- Code generation
- Computer architecture
- Stack-frame management
- Register and temporary management
- Control-flow code generation
- Memory access and pointer handling
- Debugging complex software systems

## Portfolio Summary

This repository is meant to show the structure and implementation approach for the compiler backend portion of the project. The full compiler framework is not included, but the provided files demonstrate the core backend code-generation logic used to translate typed AST nodes into RISC-V-style assembly.
