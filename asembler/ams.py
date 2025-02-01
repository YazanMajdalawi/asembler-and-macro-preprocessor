import sys

input_file_name = 'test_input.txt'
output_file_name = 'asm_output.txt'

source_code = ''
output = ''
symtab = {}
prog_length = -1
prog_name = ''
first_exe_inst = ''
optab = {
    'stl':'14', 'jsub':'48', 'lda':'00', 'comp':'28', 'jeq':'30',
    'J':'3c','sta':'0c', 'ldl':'08', 'rsub':'4c', 'ldx':'04', 'td':'e0',
    'rd':'d8','stch':'54', 'tix':'2c', 'jlt':'38', 'stx':'10', 'ldch':'50', 'wd':'dc'
}
locations = []


directives = ['start', 'base', 'word', 'resb', 'resw', 'byte']

def get_directive_len(directive, operand = ''):
    known = {'start':0, 'base':0, 'word': 3}
    if directive in known:
        return known[directive]
    if directive == 'resw':
        return 3 * int(operand)
    if directive == 'resb':
        return int(operand)
    if directive == 'byte':
        byte_type = operand[0] # first letter of the operand, could be c for char, or x for hex.
        remaining_length = (len(operand) - 3) / (1 if byte_type == 'c' else 2)
        return int(remaining_length)

def get_source():
    global source_code
    with open(input_file_name, 'r') as file:
        source_code = file.read()

def write_output():
    with open(output_file_name, 'w') as file:
        file.write(output)

def is_comment(line):
    return line[0] == '.'

def is_directive(directive):
    return directive in directives

def is_inst(inst):
    return inst in optab

def is_valid(line):
    parsed_line = parse_line(line)
    return parsed_line['opcode'] in optab or parsed_line['opcode'] in directives

def parse_line(line):
    tokens = line.split('\t')
    if is_comment(line):
        return {}
    ret = {'label': tokens[0], 'opcode': tokens[1], 'operand': tokens[2]}
    return ret

def find_start():
    global prog_name
    for line in get_lines():
        first_line = line
        if not is_comment(line):
            break
    first_line_parsed = parse_line(first_line)

    if (first_line_parsed['opcode'] != 'start'):
        return 0

    prog_name = first_line_parsed['label'] 
    return int(first_line_parsed['operand'])
  
def get_lines():
    return source_code.split('\n')

def display_symtab():  # print the table
    print()
    print('{:<10} {:<10}'.format('Symbol', 'Location'))
    for sym, loc in symtab.items():
        print('{:<10} {:<10}'.format(sym, loc))

def display_line_loc(loc, line):
    parsed_line = parse_line(line)
    print('{:<8} {:<8} {:<8} {:<8}'.format(loc, parsed_line['label'], parsed_line['opcode'], parsed_line['operand']))

def get_label(line):
    return parse_line(line)['label']

def get_objcode_len(line):
    # comment line
    if is_comment(line):
        return 0
    
    parsed_line = parse_line(line)

    # directive case
    if is_directive(parsed_line['opcode']):
        return get_directive_len(parsed_line['opcode'], parsed_line['operand'])

    # executable instruction case
    return 3


def pass_1():
    global prog_length
    start = find_start()
    loc = start
    
    for line in get_lines():
        locations.append(loc)
        if len(line) == 0 or is_comment(line):
            continue

        if not is_valid(line):
            print("Invalid instruction or directive: \n" + line)
            sys.exit(1)

        label = get_label(line)

        if label != '':
            if label in symtab:
                sys.exit(1)
            else:
                symtab[label] = loc

        display_line_loc(loc, line)
        loc += get_objcode_len(line)
    
    prog_length = loc - start


def is_indexed(line):
    parsed_line = parse_line(line)
    return parsed_line['operand'][-2:] == ',x'

#adds a number of padding zeros to the left of provided string
def add_zeros(str, zeros):
    diff = zeros - len(str)
    if(diff > 0):
        return '0' * diff + str
    return str

def char_to_hex(char):
    return f"{ord(char):02X}"

def line_objcode(line):
    objcode = ''
    parsed_line = parse_line(line)
    opcode = parsed_line['opcode']
    operand = parsed_line['operand']
    #instruction case
    if is_inst(opcode):
        objcode += optab[opcode]
        if is_indexed(line):
            if operand[:-2] in symtab:
                objcode += str(symtab[operand[:-2]])
                temp = int(objcode, 16) + 0x8000
                objcode = hex(temp)[2:]
            else:
                print('Error: unknown label: ' + operand[:-2])
                sys.exit(1)
        else:
            if operand in symtab:
                objcode += str(symtab[operand])
            elif operand == '':
                objcode += '0000'
            else:
                print('Error: unknown label: ' + operand)
                sys.exit(1)
    #directive case
    elif is_directive(opcode):
        if opcode == 'word':
            objcode = add_zeros(hex(int(operand))[2:], 6)
        elif opcode == 'byte':
            if operand[0] == 'c':
                chars = operand[2:-1]
                for char in chars:
                    objcode += char_to_hex(char)
            elif operand[0] == 'x':
                objcode = operand[2:-1]
        else:
            objcode = ''
    
    return objcode

def add_header_rec():
    global output
    start = add_zeros(str(find_start()), 6)
    output += f'h|{prog_name:6}|{start:6}|{add_zeros(str(prog_length), 6)}\n'

def add_end_rec():
    global output
    output += f'e|{add_zeros(str(first_exe_inst), 6)}'



def pass_2():
    global output, first_exe_inst
    add_header_rec()

    t_record = ''
    trec_code_len = 0
    i = 0
    for line in get_lines():
        if len(line) == 0:
            continue
        if is_comment(line):
            i += 1
            continue
        parsed_line = parse_line(line)
        opcode = parsed_line['opcode']
        if first_exe_inst == '' and opcode in optab:
            first_exe_inst = locations[i]
            
        label = parsed_line['label']
        operand = parsed_line['operand']
        print('{:<8} {:<8} {:<8} {:<8}'.format(label, opcode, operand, line_objcode(line)))

        objcode = line_objcode(line)

        # build and append t-records
        if(trec_code_len == 0 and not(opcode == 'resb' or opcode == 'resw')):
            t_record = f't|{add_zeros(str(locations[i]), 6)}|--|{objcode}'
            trec_code_len += len(objcode)


        elif opcode == 'resb' or opcode == 'resw':
            if trec_code_len == 0:
                i+=1
                continue
            t_record = t_record.replace('--', add_zeros(hex(trec_code_len//2)[2:], 2))
            output += (t_record + '\n')
            trec_code_len = 0

        elif len(objcode) + trec_code_len <= 20:
            t_record += objcode
            trec_code_len += len(objcode)
        else:
            t_record = t_record.replace('--', add_zeros(hex(trec_code_len//2)[2:], 2))
            output += t_record + '\n'
            trec_code_len = 0
            t_record = f't|{add_zeros(str(locations[i]), 6)}|--|{objcode}'
            trec_code_len += len(objcode)

        i += 1
    if trec_code_len > 0:
        t_record = t_record.replace('--', add_zeros(hex(trec_code_len//2)[2:], 2))
        output += t_record + '\n'
        trec_code_len = 0

    add_end_rec()

    write_output()




if __name__ == '__main__':
    get_source()
    pass_1()
    print()
    display_symtab()
    print()
    pass_2()
    print()
    print(output)