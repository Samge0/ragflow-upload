#!/bin/bash

TCL_PATH=$(python3 -c "
import os
import tkinter
tkinter_path = os.path.dirname(tkinter.__file__)
tcl_path = os.path.join(tkinter_path, 'tcl8.6')
tk_path = os.path.join(tkinter_path, 'tk8.6')
print(f'{tcl_path}:{tk_path}')
")

export TCL_LIBRARY=$(echo $TCL_PATH | cut -d: -f1)
export TK_LIBRARY=$(echo $TCL_PATH | cut -d: -f2)

echo "使用 TCL_LIBRARY: $TCL_LIBRARY"
echo "使用 TK_LIBRARY: $TK_LIBRARY"

./RagFlowUpload 