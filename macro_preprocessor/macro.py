import sys

input_file_name = 'input.txt'
output_file_name = 'output.txt'

deftab = {}
input = ''
output = ''

is_expanding = False

def read_input():
    global input
    with open(input_file_name, 'r') as input_file:
        input = input_file.read()

def write_output():
    with open(output_file_name, 'w') as output_file:
        output_file.write(output)

def get_lines():
    return input.split('\n')
    
def define_line(line, macro_name):
    deftab[macro_name]['unparsed_lines'].append(line)
    parsed_line = parse_line(line)
    deftab[macro_name]['lines'].append(parsed_line)

def is_macro_inst(line):
    return line['opcode'] == 'macro'

def define_macro_header(line):
    parameters = line['operand'].split(',')
    deftab[line['label']] = {'parameters':parameters , 'lines':[], 'unparsed_lines':[]}

def is_comment(line):
    return line[0] == '.'

def parse_line(line):
    tokens = line.split('\t')
    # print(tokens)
    if is_comment(line):
        return {}
    ret = {'label': tokens[0], 'opcode': tokens[1], 'operand': tokens[2]}
    return ret

def unparse_line(line):
    values = line.values()
    return '\t'.join(values)

def output_line(line):
    global output
    output += line + '\n'

def display_deftab():
    print()
    print('{:<8} {:<8} {:<10} {:<12}'.format('Macro', 'Label', 'Opcode', 'Operand'))
    for macro_name, macro_details in deftab.items():
        print()
        parameters = ', '.join(macro_details['parameters'])
        print('{:<8} {:<8} {:<10} {:<12}'.format(macro_name, '', '', parameters))
        for line in macro_details['lines']:
            print('{:<8} {:<8} {:<10} {:<12}'.format('', line['label'], line['opcode'], line['operand']))
    print()


def replace_parameters(line, formal_params, passed_params):
    if len(formal_params) != len(passed_params):
        print("\nError: incorrect number of parameters passed to macro invocation.\n")
        sys.exit(1)
    for i in range(0, len(formal_params)):
        line = line.replace(formal_params[i], passed_params[i])
    return line
            

def main_loop(invocation_line = ''):
    global is_expanding
    defining = False
    currently_defining = ''
    source = get_lines()

    if is_expanding:
        macro_name = parse_line(invocation_line)['opcode']
        source = deftab[macro_name]['unparsed_lines']
        formal_params = deftab[macro_name]['parameters']
        passed_params = parse_line(invocation_line)['operand'].split(',')

        deftab[macro_name]['lines'][0]['label'] = parse_line(invocation_line)['label']
        source[0] = unparse_line(deftab[macro_name]['lines'][0])

    inner_mends = 0
    
    for line in source:
        # print(line)
        if is_expanding:
            # print(formal_params)
            line = replace_parameters(line, formal_params, passed_params)

        if(len(line) == 0):
            continue

        if is_comment(line):
            if defining:
                continue
            else:
                output_line(line)
                continue

        parsed_line = parse_line(line)

        if defining and not is_expanding and is_macro_inst(parsed_line):
            inner_mends += 1


        if parsed_line['opcode'] == 'mend':
            if defining:
                if inner_mends == 0: # reached the last mend in the current macro
                    # print(line)
                    define_line(line, currently_defining)
                    defining = False
                    currently_defining = ''
                    continue
                else:
                    define_line(line, currently_defining)
                    inner_mends -= 1
                    continue
            else:
                deftab[macro_name]['lines'][0]['label'] = ''
                source[0] = unparse_line(deftab[macro_name]['lines'][0])
                is_expanding = False
                continue


        if defining:
            define_line(line, currently_defining)
            continue

        if is_macro_inst(parsed_line) and not defining:
            if parsed_line['label'] in deftab:
                print(f"\nError: Macro {parsed_line['label']} already exists in DEFTAB.\n")
                sys.exit(1)
            defining = True
            currently_defining = parsed_line['label']
            define_macro_header(parsed_line)
            continue
        
        # expanding
        if parsed_line['opcode'] in deftab:
            is_expanding = True
            main_loop(line)
            continue

        output_line(line)

    

if __name__ == '__main__':

    read_input()
    main_loop()
    display_deftab()
    write_output()
