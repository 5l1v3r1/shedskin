'''
*** SHED SKIN Python-to-C++ Compiler ***
Copyright 2005-2011 Mark Dufour; License GNU GPL version 3 (See LICENSE)

annotate.py: annotate source code with inferred types, as *.ss.py (shedskin -a)

'''
import re
from compiler.ast import Const, AssTuple, AssList, Assign, AugAssign, \
    Getattr, Dict, Print, Return, Printnl, Name, List, Tuple, ListComp

from config import getgx
from graph import getmv, setmv, FakeGetattr, FakeGetattr2, FakeGetattr3
from infer import inode, merged
from python import assign_rec
from typestr import nodetypestr


def annotate():
    if not getgx().annotation:
        return
    re_comment = re.compile(r'#[^\"\']*$')

    def paste(expr, text):
        if not expr.lineno:
            return
        if (expr, 0, 0) not in getgx().cnode or inode(expr).mv != mv:
            return  # XXX
        line = source[expr.lineno - 1]
        match = re_comment.search(line)
        if match:
            line = line[:match.start()]
        if text:
            text = '# ' + text
        line = line.rstrip()
        if text and len(line) < 40:
            line += (40 - len(line)) * ' '
        source[expr.lineno - 1] = line
        if text:
            source[expr.lineno - 1] += ' ' + text
        source[expr.lineno - 1] += '\n'

    for module in getgx().modules.values():
        if module.builtin:
            continue

        mv = module.mv
        setmv(mv)

        # merge type information for nodes in module XXX inheritance across modules?
        merge = merged([n for n in getgx().types if n.mv == mv], inheritance=True)

        source = open(module.filename).readlines()

        # --- constants/names/attributes
        for expr in merge:
            if isinstance(expr, (Const, Name)):
                paste(expr, nodetypestr(expr, inode(expr).parent, False))
        for expr in merge:
            if isinstance(expr, Getattr):
                paste(expr, nodetypestr(expr, inode(expr).parent, False))
        for expr in merge:
            if isinstance(expr, (Tuple, List, Dict)):
                paste(expr, nodetypestr(expr, inode(expr).parent, False))

        # --- instance variables
        funcs = getmv().funcs.values()
        for cl in getmv().classes.values():
            labels = [var.name + ': ' + nodetypestr(var, cl, False) for var in cl.vars.values() if var in merge and merge[var] and not var.name.startswith('__')]
            if labels:
                paste(cl.node, ', '.join(labels))
            funcs += cl.funcs.values()

        # --- function variables
        for func in funcs:
            if not func.node or func.node in getgx().inherited:
                continue
            vars = [func.vars[f] for f in func.formals]
            labels = [var.name + ': ' + nodetypestr(var, func, False) for var in vars if not var.name.startswith('__')]
            paste(func.node, ', '.join(labels))

        # --- callfuncs
        for callfunc, _ in getmv().callfuncs:
            if isinstance(callfunc.node, Getattr):
                if not isinstance(callfunc.node, (FakeGetattr, FakeGetattr2, FakeGetattr3)):
                    paste(callfunc.node.expr, nodetypestr(callfunc, inode(callfunc).parent, False))
            else:
                paste(callfunc.node, nodetypestr(callfunc, inode(callfunc).parent, False))

        # --- higher-level crap (listcomps, returns, assignments, prints)
        for expr in merge:
            if isinstance(expr, ListComp):
                paste(expr, nodetypestr(expr, inode(expr).parent, False))
            elif isinstance(expr, Return):
                paste(expr, nodetypestr(expr.value, inode(expr).parent, False))
            elif isinstance(expr, (AssTuple, AssList)):
                paste(expr, nodetypestr(expr, inode(expr).parent, False))
            elif isinstance(expr, (Print, Printnl)):
                paste(expr, ', '.join(nodetypestr(child, inode(child).parent, False) for child in expr.nodes))

        # --- assignments
        for expr in merge:
            if isinstance(expr, Assign):
                pairs = assign_rec(expr.nodes[0], expr.expr)
                paste(expr, ', '.join(nodetypestr(r, inode(r).parent, False) for (l, r) in pairs))
            elif isinstance(expr, AugAssign):
                paste(expr, nodetypestr(expr.expr, inode(expr).parent, False))

        # --- output annotated file (skip if no write permission)
        try:
            out = open(module.filename[:-3] + '.ss.py', 'w')
            out.write(''.join(source))
            out.close()
        except IOError:
            pass
