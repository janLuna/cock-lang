#!/usr/bin/env python3

import subprocess
from pathlib import Path
import time
import sys

from os.path import expanduser

class logger:
	def __call__(self,nam,msg):
		print(f"\u001b[1m\u001b[34;1m[{nam}]\u001b[0m",msg)
	def error(self,*args):
		if len(args) >= 2:
			args = list(args)
			nam = args.pop(0)
			print(f"\u001b[1m\u001b[31;1m[\u001b[37;1m{nam} > \u001b[31;1mERROR]\u001b[0m"," ".join(args),file=sys.stderr)
		else:
			print(f"\u001b[1m\u001b[31;1m[ERROR]\u001b[0m"," ".join(args), file=sys.stderr)

class enum:
	def __init__(self,*args):
		cnt = 0
		for prop in args:
			setattr(self, prop, cnt)
			cnt += 1

TOK = enum(
	"WORD",
	"INT",
	"STR",
	"BOOL",
)

def find_col(text,start,check):
	while start < len(text) and not check(text[start]):
		start += 1
	return start

def lex_line(line):
	col = find_col(line, 0, lambda x: not x.isspace())
	while col < len(line):
		if line[col] == '"':
			col_end = find_col(line, col+1, lambda x: x == '"')
			word = line[col+1:col_end]
			yield (col, TOK.STR, bytes(word,"utf-8").decode("unicode_escape"))
			col = find_col(line, col_end+1, lambda x: not x.isspace())
		elif line[col] == '$':
			break
		else:
			col_end = find_col(line, col, lambda x: x.isspace())
			word = line[col:col_end]
			try: yield (col, TOK.INT, int(word))
			except:
				if word in ["true","false"]: yield (col, TOK.BOOL, bool(word))
				else: yield (col, TOK.WORD, word)
			col = find_col(line, col_end, lambda x: not x.isspace())

def lex_file(fpath):
	with open(fpath,"r") as f:
		return [Token(loc=(fpath,line,col), type=toktype, value=value) for (line, text) in enumerate(f.readlines()) for (col, toktype, value) in lex_line(text)]

class Oper:
	def __init__(self,type,token,**kwargs):
		self.type = type
		self.token = token
		self.arg = kwargs.get("arg")
		self.jmp = kwargs.get("jmp")
		self.end = kwargs.get("end")

class Token:
	def __init__(self,loc,type,value):
		self.loc = loc
		self.type = type
		self.value = value

MEM = 1_280_000

COCK_IMPORTPATHS = [".","~/.local/cock/libs","/usr/local/lib"]

OP = enum(
	"PUSH",
	"PUSH_STR",
	"SUM",
	"SUBST",
	"DUMP",
	"EQ",
	"IF",
	"END",
	"SYS0",
	"SYS1",
	"SYS2",
	"SYS3",
	"SYS4",
	"SYS5",
	"SYS6",
	"SWAP",
	"DROP",
	"ROT",
	"DUP",
	"MEM",
	"DDUP",
	"STORE",
	"LOAD",
	"WHILE",
	"DO",
	"GT",
	"GE",
	"LT",
	"LE",
	"NEQ",
	"IMPORT",
	"MACRO",
	"MUL",
	"DIV",
	"AND",
	"OR",
	"XOR",
	"NOT",
	"ELSE",
	"CALL",
	"BSR",
	"BSL",
	"ELIF",
	"CONST",
	"PUSH_CONST",
)

def dict_index(dic,key):
	return list(dic.keys()).index(key)

def cockpile_nasm_linux_x86_elf64(prog,fp):
	strs = []
	with open(fp.with_suffix(".asm"),"w") as out:
		out.write("section .text\n")
		out.write("global _start\n")
		out.write("dump:\n")
		out.write("  mov r9, -3689348814741910323\n")
		out.write("  sub rsp, 40\n")
		out.write("  mov BYTE [rsp+31], 10\n")
		out.write("  lea rcx, [rsp+30]\n")
		out.write(".L2:\n")
		out.write("  mov rax, rdi\n")
		out.write("  lea r8, [rsp+32]\n")
		out.write("  mul r9\n")
		out.write("  mov rax, rdi\n")
		out.write("  sub r8, rcx\n")
		out.write("  shr rdx, 3\n")
		out.write("  lea rsi, [rdx+rdx*4]\n")
		out.write("  add rsi, rsi\n")
		out.write("  sub rax, rsi\n")
		out.write("  add eax, 48\n")
		out.write("  mov BYTE [rcx], al\n")
		out.write("  mov rax, rdi\n")
		out.write("  mov rdi, rdx\n")
		out.write("  mov rdx, rcx\n")
		out.write("  sub rcx, 1\n")
		out.write("  cmp rax, 9\n")
		out.write("  ja .L2\n")
		out.write("  lea rax, [rsp+32]\n")
		out.write("  mov edi, 1\n")
		out.write("  sub rdx, rax\n")
		out.write("  xor eax, eax\n")
		out.write("  lea rsi, [rsp+32+rdx]\n")
		out.write("  mov rdx, r8\n")
		out.write("  mov rax, 1\n")
		out.write("  syscall\n")
		out.write("  add rsp, 40\n")
		out.write("  ret\n")
		out.write("_start:\n")
		out.write("mov rax, ret_stack_end\n")
		out.write("mov [ret_stack_rsp], rax\n")
		def op_to_asm(prog):
			for op in prog:
				match op.type:
					case OP.PUSH:
						out.write(f"push %d\n" % op.arg)
					case OP.PUSH_STR:
						out.write("mov rax, %d\n" % len(op.arg))
						out.write("push rax\n")
						out.write("push str_%d\n" % len(strs))
						strs.append(op.arg)
					case OP.SUM:
						out.write("pop rax\n")
						out.write("pop rbx\n")
						out.write("add rax,rbx\n")
						out.write("push rax\n")
					case OP.SUBST:
						out.write("pop rax\n")
						out.write("pop rbx\n")
						out.write("sub rbx,rax\n")
						out.write("push rbx\n")
					case OP.DUMP:
						out.write("pop rdi\n")
						out.write("call dump\n")
					case OP.EQ:
						out.write("mov rcx, 0\n")
						out.write("mov rdi, 1\n")
						out.write("pop rax\n")
						out.write("pop rbx\n")
						out.write("cmp rax,rbx\n")
						out.write("cmove rcx,rdi\n")
						out.write("push rcx\n")
					case OP.NEQ:
						out.write("mov rcx, 0\n")
						out.write("mov rdi, 1\n")
						out.write("pop rax\n")
						out.write("pop rbx\n")
						out.write("cmp rax,rbx\n")
						out.write("cmovne rcx,rdi\n")
						out.write("push rcx\n")
					case OP.GT:
						out.write("mov rcx, 0\n")
						out.write("mov rdi, 1\n")
						out.write("pop rbx\n")
						out.write("pop rax\n")
						out.write("cmp rax,rbx\n")
						out.write("cmovg rcx,rdi\n")
						out.write("push rcx\n")
					case OP.GE:
						out.write("mov rcx, 0\n")
						out.write("mov rdi, 1\n")
						out.write("pop rbx\n")
						out.write("pop rax\n")
						out.write("cmp rax,rbx\n")
						out.write("cmovge rcx,rdi\n")
						out.write("push rcx\n")
					case OP.LT:
						out.write("mov rcx, 0\n")
						out.write("mov rdi, 1\n")
						out.write("pop rbx\n")
						out.write("pop rax\n")
						out.write("cmp rax,rbx\n")
						out.write("cmovl rcx,rdi\n")
						out.write("push rcx\n")
					case OP.LE:
						out.write("mov rcx, 0\n")
						out.write("mov rdi, 1\n")
						out.write("pop rbx\n")
						out.write("pop rax\n")
						out.write("cmp rax,rbx\n")
						out.write("cmovle rcx,rdi\n")
						out.write("push rcx\n")
					case OP.IF:
						out.write(";; if\n")
						pass
					case OP.END:
						out.write(";; end\n")
						if op.jmp:
							out.write("jmp addr_%d\n" % op.jmp)
						out.write("addr_%d:\n" % op.arg)
					case OP.SYS6:
						out.write("pop rax\n")
						out.write("pop rdi\n")
						out.write("pop rsi\n")
						out.write("pop rdx\n")
						out.write("pop r10\n")
						out.write("pop r8\n")
						out.write("pop r9\n")
						out.write("syscall\n")
						out.write("push rax\n")
					case OP.SYS5:
						out.write("pop rax\n")
						out.write("pop rdi\n")
						out.write("pop rsi\n")
						out.write("pop rdx\n")
						out.write("pop r10\n")
						out.write("pop r8\n")
						out.write("syscall\n")
						out.write("push rax\n")
					case OP.SYS4:
						out.write("pop rax\n")
						out.write("pop rdi\n")
						out.write("pop rsi\n")
						out.write("pop rdx\n")
						out.write("pop r10\n")
						out.write("syscall\n")
						out.write("push rax\n")
					case OP.SYS3:
						out.write("pop rax\n")
						out.write("pop rdi\n")
						out.write("pop rsi\n")
						out.write("pop rdx\n")
						out.write("syscall\n")
						out.write("push rax\n")
					case OP.SYS2:
						out.write("pop rax\n")
						out.write("pop rdi\n")
						out.write("pop rsi\n")
						out.write("syscall\n")
						out.write("push rax\n")
					case OP.SYS1:
						out.write("pop rax\n")
						out.write("pop rdi\n")
						out.write("syscall\n")
						out.write("push rax\n")
					case OP.SYS0:
						out.write("pop rax\n")
						out.write("syscall\n")
						out.write("push rax\n")
					case OP.SWAP:
						out.write("pop rax\n")
						out.write("pop rbx\n")
						out.write("push rax\n")
						out.write("push rbx\n")
					case OP.DROP:
						out.write("pop rax\n")
					case OP.ROT:
						out.write("pop rax\n")
						out.write("pop rbx\n")
						out.write("pop rcx\n")
						out.write("push rbx\n")
						out.write("push rax\n")
						out.write("push rcx\n")
					case OP.DUP:
						out.write("pop rax\n")
						out.write("push rax\n")
						out.write("push rax\n")
					case OP.DDUP:
						out.write("pop rax\n")
						out.write("pop rbx\n")
						out.write("push rbx\n")
						out.write("push rax\n")
						out.write("push rbx\n")
						out.write("push rax\n")
					case OP.MEM:
						out.write("push mem\n")
					case OP.STORE:
						out.write("pop rbx\n")
						out.write("pop rax\n")
						out.write("mov [rax],bl\n")
					case OP.LOAD:
						out.write("pop rax\n")
						out.write("xor rbx,rbx\n")
						out.write("mov bl,[rax]\n")
						out.write("push rbx\n")
					case OP.WHILE:
						out.write("addr_%d:\n" % op.arg)
					case OP.DO:
						out.write("pop rax\n")
						out.write("cmp rax,1\n")
						out.write("jne addr_%d\n" % op.jmp)
					case OP.MUL:
						out.write("pop rax\n")
						out.write("pop rbx\n")
						out.write("mul rbx\n")
						out.write("push rax\n")
					case OP.DIV:
						out.write("pop rbx\n")
						out.write("pop rax\n")
						out.write("cqo\n")
						out.write("div rbx\n")
						out.write("push rdx\n")
						out.write("push rax\n")
					case OP.AND:
						out.write("pop rax\n")
						out.write("pop rbx\n")
						out.write("and rax,rbx\n")
						out.write("push rax\n")
					case OP.OR:
						out.write("pop rax\n")
						out.write("pop rbx\n")
						out.write("or rax,rbx\n")
						out.write("push rax\n")
					case OP.XOR:
						out.write("pop rax\n")
						out.write("pop rbx\n")
						out.write("xor rax,rbx\n")
						out.write("push rax\n")
					case OP.ELSE:
						out.write(";; else\n")
						out.write("jmp addr_%d\n" % op.jmp)
						out.write("addr_%d:\n" % op.arg)
					case OP.NOT:
						out.write("pop rax\n")
						out.write("not rax\n")
						out.write("push rax\n")
					case OP.CALL:
						out.write("mov rax, rsp\n")
						out.write("mov rsp, [ret_stack_rsp]\n")
						out.write("call fun_%d\n" % op.arg)
						out.write("mov [ret_stack_rsp], rsp\n")
						out.write("mov rsp, rax\n")
					case OP.BSL:
						out.write("pop rcx\n")
						out.write("pop rbx\n")
						out.write("shl rbx,cl\n")
						out.write("push rbx\n")
					case OP.BSR:
						out.write("pop rcx\n")
						out.write("pop rbx\n")
						out.write("shr rbx,cl\n")
						out.write("push rbx\n")
					case OP.ELIF:
						out.write(";; elif\n")
						out.write("jmp addr_%d\n" % op.end)
						out.write("addr_%d:\n" % op.arg)
					case OP.PUSH_CONST:
						out.write("push qword [const_%d]\n" % op.arg)
					case _:
						log.error(format_loc(op.token.loc),f"Operation type of token `{op.token.value}` isn't handled, this is probably a bug")
						exit(1)
		op_to_asm(prog)
		out.write("mov rax,60\n")
		out.write("mov rdi,0\n")
		out.write("syscall\n")
		for fun in macros:
			out.write("fun_%d:\n" % dict_index(macros,fun))
			out.write("mov [ret_stack_rsp], rsp\n")
			out.write("mov rsp, rax\n")
			op_to_asm(compile_prog(macros[fun]))
			out.write("mov rax, rsp\n")
			out.write("mov rsp, [ret_stack_rsp]\n")
			out.write("ret\n")
		out.write("segment .data\n")
		for i, s in enumerate(strs):
			out.write("str_%d:\n" % i)
			out.write("db %s\n" % ','.join(map(hex, list(bytes(s, 'utf-8')))))
		for const in consts:
			out.write("const_%d:\n" % dict_index(consts,const))
			if consts[const].type == TOK.STR: out.write("db %s\n" % ','.join(map(hex, list(bytes(consts[const].value, 'utf-8')))))
			else: out.write("db %d\n" % consts[const].value)
		out.write("segment .bss\n")
		out.write("mem: resb %d\n" % MEM)
		out.write("ret_stack_rsp: resq 1\n")
		out.write("ret_stack: resb %d\n" % MEM)
		out.write("ret_stack_end:\n")
		out.close()

log = logger()

BUILTINS = {
	"+": OP.SUM,
	"-": OP.SUBST,
	"dump": OP.DUMP,
	"=": OP.EQ,
	"if": OP.IF,
	"end": OP.END,
	"syscall0": OP.SYS0,
	"syscall1": OP.SYS1,
	"syscall2": OP.SYS2,
	"syscall3": OP.SYS3,
	"syscall4": OP.SYS4,
	"syscall5": OP.SYS5,
	"syscall6": OP.SYS6,
	"swap": OP.SWAP,
	"drop": OP.DROP,
	"rot": OP.ROT,
	"dup": OP.DUP,
	"ddup": OP.DDUP,
	"mem": OP.MEM,
	".": OP.STORE,
	",": OP.LOAD,
	"while": OP.WHILE,
	"do": OP.DO,
	"!=": OP.NEQ,
	">": OP.GT,
	"<": OP.LT,
	">=": OP.GE,
	"<=": OP.LE,
	"import": OP.IMPORT,
	"fun": OP.MACRO,
	"*": OP.MUL,
	"/": OP.DIV,
	"&": OP.AND,
	"||": OP.OR,
	"|": OP.XOR,
	"!": OP.NOT,
	"else": OP.ELSE,
	"<<": OP.BSL,
	">>": OP.BSR,
	"elif": OP.ELIF,
	"const": OP.CONST,
}

macros = {}
consts = {}

lastaddr = -1

prev_imports = []

def compile_prog(tokens):
	ifs = []
	refs = []
	program = []
	rtokens = list(reversed(tokens))
	i = 0;
	def word_to_op(token):
		if token.type == TOK.WORD:
			if token.value in BUILTINS:
				return Oper(type=BUILTINS[token.value], token=token)
			elif token.value in macros:
				return Oper(type=OP.CALL, token=token, arg=dict_index(macros,token.value))
			elif token.value in consts:
				return Oper(type=OP.PUSH_CONST, token=token, arg=dict_index(consts,token.value))
			else:
				log.error(format_loc(token.loc),f"Word `{token.value}` isn't defined.")
				exit(1)
		elif token.type in [TOK.INT, TOK.BOOL]:
			return Oper(type=OP.PUSH, token=token, arg=int(token.value))
		elif token.type == TOK.STR:
			return Oper(type=OP.PUSH_STR, token=token, arg=token.value)
	while len(rtokens) > 0:
		op = word_to_op(rtokens.pop())
		if op.type == OP.IMPORT:
			imported = rtokens.pop()
			importpath = None

			for path in COCK_IMPORTPATHS:
				path = Path(path).expanduser().joinpath(imported.value).absolute()
				if path.exists():
					importpath = path
					break

			if importpath == None:
				log.error(format_loc(op.token.loc), f"File `{importpath}` does not exist")
				exit(1)
			elif importpath.name not in prev_imports:
				prev_imports.append(importpath.name)
				try: rtokens += reversed(lex_file(importpath))
				except:
					log.error(format_loc(op.token.loc),f"Failed to import `{importpath}`")
					exit(1)

		elif op.type == OP.END:
			global lastaddr
			ind = ifs.pop()
			lastaddr += 1
			op.arg = lastaddr
			if program[ind].type in [OP.DO, OP.ELSE]:
				ind2 = ifs.pop()
				if program[ind2].type == OP.WHILE:
					program[ind].jmp = lastaddr
					lastaddr += 1
					program[ind2].arg = lastaddr
					op.jmp = lastaddr
				elif program[ind2].type in [OP.IF,OP.ELIF, OP.ELSE]:
					program[ind].jmp = lastaddr
					program[ind2].end = lastaddr
					if len(refs) == 0: lastaddr += 1
					while len(refs) > 0:
						if len(ifs) > 1: ifs.pop()
						program[refs.pop()].end = lastaddr
				else:
					log.error(format_loc(op.token.loc),"`do` can only be used with `while`, `if` and `elif`")
					exit(1)
			else:
				log.error(format_loc(op.token.loc),f"`end` was used to close a nonexistant block")
				exit(1)
			program.append(op)
			i += 1
		elif op.type == OP.MACRO:
			macro = rtokens.pop()
			if macro.value in macros:
				log.error(format_loc(macro.loc),f"Attempted to redefine existing function `{macro.value}`.")
				exit(1)
			if macro.value in BUILTINS:
				log.error(format_loc(macro.loc),f"Attempted to redefine a builtin.")
				exit(1)
			macros[macro.value] = []
			blocks = 0
			while len(rtokens) > 0:
				token = rtokens.pop()
				if token.value in ["if","while","const","fun"]: blocks += 1
				elif token.value == "end":
					if blocks == 0: break
					else: blocks -= 1
				macros[macro.value].append(token)
		elif op.type == OP.CONST:
			name=rtokens.pop()
			value=rtokens.pop()
			end=rtokens.pop()
			if name.type != TOK.WORD:
				log.error(format_loc(name.loc), "The name of a constant must be a `word`")
				exit(1)
			if value.type == TOK.WORD:
				log.error(format_loc(value.loc), "The value of a constant can't be a `word`")
				exit(1)
			if end.value != "end":
				log.error(format_loc(end.loc),"Constant must be closed with `end`")
				exit(1)
			consts[name.value] = value
		elif op.type in [OP.ELSE, OP.ELIF]:
			ind = ifs.pop()
			assert program[ind].type in [OP.DO], "[ERROR] `else` can only be used with `if` and `elif` statements"
			program[ind].jmp = i
			op.arg = i
			refs.append(i)
		elif op.type not in [OP.IF,OP.WHILE,OP.DO,OP.ELSE,OP.ELIF]:
			program.append(op)
			i += 1
		if op.type in [OP.IF,OP.WHILE,OP.DO,OP.ELSE,OP.ELIF]:
			program.append(op)
			ifs.append(i)
			i += 1
	return program

def run_cmd(cmd):
	log("CMD", " ".join(cmd))
	subprocess.call(cmd)

def format_loc(loc):
	return f"{loc[0]}:{loc[1]}:{loc[2]}"

def check_flag(flags,*args):
	result = False
	for arg in args:
		if arg in flags:
			flags.remove(arg)
			result = True
	return result

def check_flag_arg(flags,*args):
	result = False
	for arg in args:
		if arg in flags:
			flagindex = flags.index(arg)
			if len(flags) >= flagindex + 2:
				result = flags[flagindex + 1]
	return result

if __name__ == "__main__":
	from sys import argv
	
	if len(argv) < 2 or check_flag(argv,"-h","--help"):
		log.error("You must provide a file to compile!")
		print(f"Usage: {argv[0]} [options] <file>")
		print(f"Options:")
		print(f"	-r --run: Runs the program after compiling.")
		print(f"	-t --temp: Writes to temporary files which get deleted after compilation. (Useful with `-r`)")
		print(f"	-q --quiet: Disables standard logging, if used twice it also disables error logging")
		print(f"	--target <target>: Sets the build target (default: nasm-linux-x86-elf64)")
		exit(1)
	else:
		run = check_flag(argv,"-r","--run")
		tmp = check_flag(argv,"-t","--temp")
		target = check_flag_arg(argv,"--target")
		if target == False: target = "nasm-linux-x86-elf64"
		match target:
			case "nasm-linux-x86-elf64":
				cockpile = cockpile_nasm_linux_x86_elf64
				asm_cmd = lambda asm: ["nasm","-felf64",asm]
				link_cmd = lambda obj, com_bin: ["ld", obj, "-o", com_bin]
				cleanup_cmd = lambda obj: ["rm", obj]
			case _:
				log.error("Unknown target specified!")
				exit(1)
		silence = 0
		if check_flag(argv,"-qq"): silence = 2
		else:
			while check_flag(argv,"-q","--quiet"):
				if silence == 2: break
				silence += 1
		if silence >= 1: logger.__call__ = lambda a,b,c: None
		if silence >= 2: log.error = lambda a,b=None: None
		prog = compile_prog(lex_file(argv[1]))
		if tmp: fp = Path(f"tmp-{time.time_ns()}-{argv[1]}")
		else: fp=Path(argv[1])
		asm = str(fp.with_suffix(".asm"))
		obj = str(fp.with_suffix(".o"))
		com_bin = str(fp.stem)
		cockpile(prog,fp)
		run_cmd(asm_cmd(asm))
		run_cmd(link_cmd(obj,com_bin))
		run_cmd(cleanup_cmd(obj))
		if run: run_cmd([f"./{com_bin}"])
		if tmp: run_cmd(["rm", asm, com_bin])
