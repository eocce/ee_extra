"""Auxiliary module store functions to translate JavaScript to Python."""

from black import format_str, FileMode
import regex
import random
import string
import re

# 1. Normalize function name
# For example: "var exp = function(x){ }" --> "function exp(x) { }"
def normalize_fn_style(x: str) -> str:
    """Normalize Javascript function style

    var xx = function(x){} --> function xx(x){}
    
    Args:
        x (str): A Js script as string.

    Returns:
        [str]: Python string
    """
    pattern = "var\s*(.*[^\s])\s*=\s*function"
    matches = re.finditer(pattern, x, re.MULTILINE)    
    for _, item in enumerate(matches):
        match = item.group(0)
        group = item.group(1)
        x = x.replace(match, f"function {group}")
    return x


# 2. Remove curly braces
# For example: "obj={'b':'a'}}" --> "obj={'b':'a'}"
def delete_brackets(x):
    counter = 0
    newstring = ""
    for char in x:
        if char == "{":
            counter += 1
        elif char == "}":
            counter -= 1
        if counter >= 0:
            newstring += char
        else:
            counter = 0
    return newstring


# 3. Remove reserved keyword "var"
# For example: "var x = 1" --> "x = 1"
def variable_definition(x):
    pattern = r"var(.*?)="
    matches = re.findall(pattern, x, re.DOTALL)
    if len(matches) > 0:
        for match in matches:
            x = x.replace(f"var{match}=", f"{match.replace(' ','')} =")
    return x


# 4. Change logical operators, boolean, null and comments
# For example: "m = s.and(that);" -> "m = s.And(that)"
def logical_operators_boolean_null_comments(x):    
    reserved = {
        ".and\(": ".And(",
        ".or\(": ".Or(",
        ".not\(": ".Not(",
        "\strue\s|\strue\n": "True",
        "\sfalse\s|\sfalse\n": "False",
        "\snull\s|\snull\n": "None",
        "//": "#",
        "!": " not "
    }    
    for key, item in reserved.items():
        x = re.sub(key, item, x)
        #x = x.replace(key, item)
    return x


# 5. /* . . . */ : Replace "/*" by "#".
def multiline_comments(x):
    pattern = r"/\*(.*?)\*/"
    matches = re.findall(pattern, x, re.DOTALL)
    if len(matches) > 0:
        for match in matches:
            x = x.replace(match, match.replace("\n", "\n#"))
    x = x.replace("/*", "#")
    return x


# 5. /* ... */: Add "#" to each line of the multiline comment block.
def multiline_method_chain(x):
    lines = x.split("\n")
    for i in range(len(lines)):
        if lines[i].replace(" ", "").startswith("."):
            lines[i - 1] = lines[i - 1] + " \\"
    return "\n".join(lines)


# 7. Random name generator
def random_fn_name():
    """Generate a random name"""        
    # body (7)
    body_list = list()
    for x in range(9):
        body_list.append(random.choice(string.ascii_letters))
    base = "".join(body_list)
    
    # number (4)
    tail_list = list()
    for x in range(6):
        tail_list.append(random.choice(string.ascii_letters+"123456789"))    
    tail = "".join(tail_list)
    return base + tail


# 8. Identify all the functions
def indentify_js_functions(x:str) -> list:
    """Identify all the functions in a Javascript file

    Args:
        x (str): A Js script as string.

    Returns:
        [list]: A list with all the functions names.
    """
    pattern = r"function\s*([A-z0-9]+)?\s*\((?:[^)(]+|\((?:[^)(]+|\([^)(]*\))*\))*\)\s*\{(?:[^}{]+|\{(?:[^}{]+|\{[^}{]*\})*\})*\}"

    matches = re.finditer(pattern, x, re.MULTILINE)
    js_functions = list()
    for _, item in enumerate(matches):
        js_functions.append(item.group())
        
    # It is a function with name?
    return js_functions


# 9. Convert simple JavaScript functions to Python
def from_js_to_py_fn_simple(js_function):
    """From Javascript to Python 1order

    Args:
        js_function (str): A Python string

    Returns:
        [dict]: Dictionary with py information
    """
    # 1. get function name
    pattern = r"function\s*([\x00-\x7F][^\s]+)\s*\(.*\)\s*{"
    regex_result = re.findall(pattern, js_function)
    
    # if it is a anonymous function
    if len(regex_result) == 0:
        anonymous = True
        function_name = random_fn_name()
    else:
        anonymous = False
        function_name = "".join(regex_result[0])
    
    # 2. get args
    pattern = r"function\s*[\x00-\x7F][^\s]*\s*\(\s*([^)]+?)\s*\)\s*{|function\(\s*([^)]+?)\s*\)\s*"
    args_name = "".join(re.findall(pattern, js_function)[0])
    
    # 3. get body
    pattern = r"({(?>[^{}]+|(?R))*})"
    body = regex.search(pattern, js_function)[0][1:-1]
    
    if not body[0] == "\n":
        body = "\n    " + body
    
    # 3. py function info
    py_info = {
        'fun_name': function_name,
        "args_name": args_name, 
        "body": body,
        "fun_py_style": f"def {function_name}({args_name}):{body}\n",
        "anonymous": anonymous
    }
    return py_info


def fix_identation(x):
    """Fix identation of a Python script"""
    ident_base = "    "
    brace_counter = 0
    
    # if first element of the string is \n remove!
    if x[0] == "\n":
        x = x[1:]
        
    # remove multiple \n by just one
    pattern = r"\n+"
    x = re.sub(pattern, r"\n", x)

    # Detect the spaces of the first identation
    x = regex.sub(r"\n\s+", "\n", x)
    
    
    
    # fix nested identation
    brace_counter = 0
    word_list = list()
    for word in x:
        if word in "{":
            brace_counter = brace_counter + 1
            word_list.append(word)
        elif word in "}":
            brace_counter = brace_counter - 1
            word_list.append(word)
        else:
            if word in "\n":
                word = "\n" + ident_base*(brace_counter)
                word_list.append(word)
            else:
                word_list.append(word)
    x_fix = "".join(word_list)

    return x_fix


def add_identation(x):
    """Add extra identation in a Python function body"""
    pattern = "\n"
    # identation in the body
    body_id = re.sub(pattern, r"\n    ", x)
    # identation in the header
    return "\n    " + body_id


def check_nested_fn_complexity(x):
    """Thi is useful to avoid errors related to catastrophic backtracking"""
    pattern = "\s{16}function"
    if re.search(pattern, x):
        raise ValueError("This module does not support 4-level nested functions.")    
    return False


def remove_extra_spaces(x):
    """Remove \n and \s if they are at the begining of the string"""
    if x[0] == "\n":        
        # Remove spaces at the beginning
        word_list = list()
        forward_counter = 0
        for word in x:
            if (word == "\n" or word.isspace()) and forward_counter == 0:
                pass
            else:
                forward_counter = -1
                word_list.append(word)
        
        # Remove spaces at the end
        back_counter = 0
        while back_counter <= 0:
            counter = back_counter - 1
            if word_list[counter] == " ":
                del(word_list[counter])                
            else:
                back_counter = 1
        return "".join(word_list)
    return x

def function_definition(x):
    
    # Check nested functionn complexity
    check_nested_fn_complexity(x)
    
    # 1. Identify all the Javascript functions
    js_functions = indentify_js_functions(x)
    
    #js_function = js_functions[0]
    
    for js_function in js_functions:
        nreturns = re.findall(r"return\s", js_function)        
        # 2. if a nested function?
        if len(nreturns) > 1:
            # 3. From js function by Python function (1 order)
            py_function = from_js_to_py_fn_simple(js_function)
            f_name = py_function["fun_name"]
            f_args = py_function["args_name"]
            header = f"def {f_name}({f_args}):\n    "
            
            # 4. From js function by Python function (2 order)
            new_body = remove_extra_spaces(py_function["body"])
            py_body = fix_identation(new_body)
            second_group = function_definition(py_body)
            second_group = add_identation(second_group)
            
            x = x.replace(js_function, header + second_group)
        else:            
            # 3. Remove Javascript function by Python function
            py_function = from_js_to_py_fn_simple(js_function)
            py_function_f = py_function["fun_py_style"]
            if py_function["anonymous"]:
                x = x.replace(js_function, py_function["fun_name"])                                
                x = "\n" + py_function_f + "\n" + x
            else:
                x = x.replace(js_function, "\n" + py_function_f)
    return x


# 7. Change "{x = 1}" by "{'x' = 1}".
def dictionary_keys(x):
    pattern = r"{(.*?)}"
    dicts = re.findall(pattern, x, re.DOTALL)
    if len(dicts) > 0:
        for dic in dicts:
            items = dic.split(",")
            for item in items:
                pattern = r"(.*):(.*)"
                item = re.findall(pattern, item)
                if len(item) > 0:
                    for i in item:
                        i = list(i)
                        j = i[0].replace('"', "").replace("'", "").replace(" ", "")
                        x = x.replace(f"{i[0]}:{i[1]}", f"'{j}':{i[1]}")
    return x


# NECESITA REVISION
# Debe cambiar el acceso a los diccionarios. Es capaz de cambiar "exports.x = 1" por "exports['x'] = 1"
# Pero cuando hay otros puntos en el texto tambien los cambia, como "https://google.com" por "https://google['com']"
# Esto es un error.
def dictionary_object_access(x):
    pattern = r"\.(.*)"
    matches = re.findall(pattern, x)
    if len(matches) > 0:
        for match in matches:
            if "=" in match:
                splitted = match.split("=")
                key = splitted[0].replace(" ", "")
                x = x.replace(f".{match}", f"['{key}'] ={splitted[1]}")
            elif (
                "(" not in match
                and ")" not in match
                and len(match) > 0
                and not any(char.isdigit() for char in match)
            ):
                x = x.replace(f".{match}", f"['{match}']")
    return x


# FUNCIONA
# Cambia "f({x = 1})" por "f(**{x = 1})"
def keyword_arguments_object(x):
    pattern = r"\((.*){(.*)}(.*)\)"
    matches = re.findall(pattern, x, re.DOTALL)
    if len(matches) > 0:
        for match in matches:
            match = list(match)
            x = x.replace("{" + match[1] + "}", "**{" + match[1] + "}")
    return x


# FUNCIONA
# Cambia "if(x){" por "if x:"
def if_statement(x):
    pattern = r"if(.*?)\((.*)\)(.*){"
    matches = re.findall(pattern, x)
    if len(matches) > 0:
        for match in matches:
            match = list(match)
            x = x.replace(
                "if" + match[0] + "(" + match[1] + ")" + match[2] + "{", f"if {match[1]}:"
            )
    return delete_brackets(x)


# FUNCIONA
# Cambia "Array.isArray(x)" por "isinstance(x,list)"
def array_isArray(x):
    pattern = r"Array\.isArray\((.*?)\)"
    matches = re.findall(pattern, x)
    if len(matches) > 0:
        for match in matches:
            x = x.replace(f"Array.isArray({match})", f"isinstance({match},list)")
    return x


# FUNCIONA
# Cambia "for(var i = 0;i < x.length;i++){" por "for i in range(0,len(x),1):"
def for_loop(x):
    pattern = r"for(.*)\((.*);(.*);(.*)\)(.*){"
    matches = re.findall(pattern, x)
    if len(matches) > 0:
        for match in matches:
            match = list(match)
            # Get the start value and the iter name
            i = match[1].replace("var ", "")
            i = i.replace(" ", "").split("=")
            start = i[1]
            i = i[0]
            # Get the end/stop value
            end = (
                match[2]
                .replace("=", " ")
                .replace(">", " ")
                .replace("<", " ")
                .replace("  ", " ")
                .split(" ")[-1]
            )
            if "." in end:
                end = end.split(".")[0]
                end = f"len({end})"
            # Get the step value
            if "++" in match[3]:
                step = 1
            elif "--" in match[3]:
                step = -1
            elif "+=" in match[3]:
                step = match[3].replace(" ", "").split("+=")[-1]
            elif "-=" in match[3]:
                step = match[3].replace(" ", "").split("+=")[-1]
                step = f"-{step}"
            x = x.replace(
                "for"
                + match[0]
                + "("
                + match[1]
                + ";"
                + match[2]
                + ";"
                + match[3]
                + ")"
                + match[4]
                + "{",
                f"for {i} in range({start},{end},{step}):",
            )
    x = x.replace(";", "")
    return delete_brackets(x)

def translate(x: str) -> str:
    """Translates a JavaScript script to a Python script.

    Args:
        x : A JavaScript script.

    Returns:
        A Python script.

    Examples:
        >>> import ee
        >>> from ee_extra.JavaScript.eejs2py import translate
        >>> ee.Initialize()
        >>> translate("var x = ee.ImageCollection('COPERNICUS/S2_SR')")
    """
    
    x = normalize_fn_style(x)
    x = variable_definition(x)
    x = logical_operators_boolean_null_comments(x)
    x = multiline_comments(x)
    x = multiline_method_chain(x)
    x = function_definition(x)
    x = dictionary_keys(x)
    x = dictionary_object_access(x)
    x = keyword_arguments_object(x)
    x = if_statement(x)
    x = array_isArray(x)
    x = for_loop(x)
    x_black = format_str(x, mode=FileMode())
    
    return x_black

if __name__ == "__main__":
    x = """
    function castCloudShadows(cloudMask, cloudHeights, sunAzimuth, sunZenith) {
        return cloudHeights.map(function (cloudHeight) {
            return projectCloudShadow(cloudMask, cloudHeight, sunAzimuth, sunZenith);
        });
    }
    """
    translate(x)