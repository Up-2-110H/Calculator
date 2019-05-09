import sys
import re

from app.error import Error

in_file = 'expressions.in'

functions = {}
variables = {}
expressions = {}


def solve_exp(exp: str, argv: dict = None):
    if argv is None:
        argv = {}

    for key, value in argv.items():
        exp = re.sub(r'((?<=[+\-*/(,])|^)' + key + r'((?=[+\-*/),])|$)', '{}'.format(value), exp)

    for key, value in variables.items():
        exp = re.sub(r'((?<=[+\-*/(,])|^)' + key + r'((?=[+\-*/),])|$)', '{}'.format(value[1]), exp)

    for func_name, func_data in functions.items():

        count = exp.count('{}('.format(func_name))
        last_found = 0

        for i in range(count):

            exp_len = len(exp)
            last_found = exp.find('{}('.format(func_name), last_found)

            if last_found == -1:
                continue

            j = last_found + len(func_name) + 1
            deep = 0
            comma = j

            arg_exps = []

            while j < exp_len and (deep != 0 or exp[j] != ')'):

                if deep == 0 and exp[j] == ',':
                    arg_exps.append(exp[comma:j])
                    comma = j + 1

                if exp[j] == '(':
                    deep += 1

                if exp[j] == ')':
                    deep -= 1

                j += 1

            if j == exp_len:
                return Error.errors['EXP_ERR'][0], 0
            else:
                if comma != last_found + len(func_name) + 1:
                    arg_exps.append(exp[comma:j])

            arg_exps_len = len(arg_exps)
            arg_data = {}

            if arg_exps_len not in func_data:
                return Error.errors['EXP_ERR'][1], 0

            for k in range(arg_exps_len):

                err, result = solve_exp(arg_exps[k])

                if err != Error.errors['SUCCESS']:
                    return err, 0

                arg_data[func_data[arg_exps_len][1][k]] = result

            err, result = solve_exp(func_data[arg_exps_len][0], arg_data)

            if err != Error.errors['SUCCESS']:
                return err, 0

            exp = exp.replace(exp[last_found:j + 1], '{}'.format(result))
            last_found = j + 1

    if re.search(r'^[0-9+\-*/%().e]*$', exp):
        try:
            result = eval(exp)
            return Error.errors['SUCCESS'], result
        except ZeroDivisionError:
            return Error.errors['EXP_ERR'][4], 0
        except:
            return Error.errors['EXP_ERR'][2], 0
    else:
        return Error.errors['EXP_ERR'][3], 0


def name_validation(name: str, is_func=False):
    if is_func:
        pattern = r'^[A-z_]+[\w]*\s*\(((\s*[A-z_]+[\w]*\s*,)*\s*[A-z_]+[\w]*\s*)?\)$'
    else:
        pattern = r'^[A-z_]+[\w]*$'

    return re.search(pattern, name) is not None


def func_handler(exp: str, is_init=True):
    exp_split = exp.split('=', 1)

    if len(exp_split) == 1:
        return Error.errors['FUNCTION_INIT_ERR'][0], None, None

    func = exp_split[0].strip()
    func_exp = re.sub(r'\s+', '', exp_split[1])

    if name_validation(func, True):
        args = re.search(r'(?<=\()[\s\S]*(?=\))', func).group(0)
        func_name = re.search(r'^\w+', func).group(0)

        argv = []
        for arg in args.split(','):
            arg_strip = arg.strip()
            if len(arg_strip):
                if arg_strip not in argv:
                    argv.append(arg_strip)
                else:
                    return Error.errors['FUNCTION_INIT_ERR'][4], None, None

        argc = len(argv)

        if func_name in functions:
            if is_init and argc in functions[func_name]:
                return Error.errors['FUNCTION_INIT_ERR'][1], None, None
            elif not is_init and argc not in functions[func_name]:
                return Error.errors['FUNCTION_INIT_ERR'][2], None, None

            functions[func_name][argc] = (func_exp, argv)
        else:
            functions[func_name] = {
                argc: (func_exp, argv)
            }

        return Error.errors['SUCCESS'], func_name, argc
    else:
        return Error.errors['FUNCTION_INIT_ERR'][3], None, None


def var_handler(exp: str, is_init=True):
    exp_split = exp.split('=', 1)

    if len(exp_split) == 1:
        return Error.errors['VAR_INIT_ERR'][0], None

    var_name = exp_split[0].strip()
    var_exp = re.sub(r'\s+', '', exp_split[1])

    if name_validation(var_name):

        if is_init and var_name in variables:
            return Error.errors['VAR_INIT_ERR'][1], None
        elif not is_init and var_name not in variables:
            return Error.errors['VAR_INIT_ERR'][2], None

        err, result = solve_exp(var_exp)

        if err == Error.errors['SUCCESS']:
            variables[var_name] = (var_exp, result)
            return err, var_name

        return err, None
    else:
        return Error.errors['VAR_INIT_ERR'][3], None


def exp_handler(exp: str):
    err, result = solve_exp(exp)

    if err == Error.errors['SUCCESS']:
        expressions[exp] = result

    return err, exp


def handler(exp: str):
    exp_split = exp.split(' ', 1)

    if exp_split[0] == 'function':
        if len(exp_split) > 1:
            err, func_name, argc = func_handler(exp_split[1].strip())

            if err == Error.errors['SUCCESS']:
                print('{} {}({}) = {};'.format(exp_split[0], func_name, str(functions[func_name][argc][1])[1:-1].replace('\'', ''), functions[func_name][argc][0]))
                return err[0]

            print('{};'.format(exp))
            print('{}\n'.format(err[1]))
            return err[0]

        else:
            print('{};'.format(exp))
            print('{}\n'.format(Error.errors['FUNCTION_INIT_ERR'][0][1]))
            return Error.errors['FUNCTION_INIT_ERR'][0][1]
    elif exp_split[0] == 'var':
        if len(exp_split) > 1:
            err, var_name = var_handler(exp_split[1].strip())

            if err == Error.errors['SUCCESS']:
                print('{} {} = {}; ({})'.format(exp_split[0], var_name, variables[var_name][0], variables[var_name][1]))
                return err[0]

            print('{};'.format(exp))
            print('{}\n'.format(err[1]))
            return err[0]
        else:
            print('{};'.format(exp))
            print('{}\n'.format(Error.errors['VAR_INIT_ERR'][0][1]))
            return Error.errors['VAR_INIT_ERR'][0][1]

    exp_split = exp.split('=', 1)

    if len(exp_split) > 1:
        if re.search(r'[()]', exp_split[0]):
            err, func_name, argc = func_handler(exp, False)

            if err == Error.errors['SUCCESS']:
                print('{}({}) = {};'.format(func_name, str(functions[func_name][argc][1])[1:-1].replace('\'', ''), functions[func_name][argc][0]))
                return err[0]

            print('{};'.format(exp))
            print('{}\n'.format(err[1]))
            return err[0]
        else:
            err, var_name = var_handler(exp, False)

            if err == Error.errors['SUCCESS']:
                print('{} = {}; ({})'.format(var_name, variables[var_name][0], variables[var_name][1]))
                return err[0]

            print('{};'.format(exp))
            print('{}\n'.format(err[1]))
            return err[0]

    err, expression = exp_handler(re.sub(r'\s+', '', exp))

    if err == Error.errors['SUCCESS']:
        print('{}={};'.format(expression, expressions[expression]))
        return err[0]

    print('{};'.format(exp))
    print('{}\n'.format(err[1]))
    return err[0]



def main(argv):
    file = open(in_file, 'r')
    expressions = file.read()
    file.close()

    exp_array = [exp.strip() for exp in expressions.split(';') if len(exp.strip())]

    for exp in exp_array:
        handler(exp)


if __name__ == "__main__":
    main(sys.argv)
