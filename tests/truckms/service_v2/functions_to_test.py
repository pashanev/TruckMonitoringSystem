from collections import Callable
import io


#TODO try to annotate like this
# Callable[[type1, type2], {'arg3': int, 'arg4': Optional[int]}, ret]
def func_return_dict(arg1, arg2) -> dict:
    return {arg1: arg2}


def func_return_val():
    return 10


def complex_func(identifier: str, int_arg: int, str_arg: str, file_arg: io.IOBase, func_arg: Callable, func_arg_ret_dict: Callable) -> dict:
    ret_dict = func_arg_ret_dict("func_arg_ret_dict_key", 10)
    assert ret_dict is not None
    val = "{},{},{},{}".format(identifier, int_arg, str_arg, func_arg(), file_arg.name)
    ret_dict = {"val": val}
    return ret_dict


def complex_func2(identifier: str, int_arg: int, str_arg: str, file_arg: io.IOBase, func_arg: Callable, func_arg_ret_dict: Callable) -> {"val":str, "results_file": io.IOBase}:
    ret_dict = func_arg_ret_dict("func_arg_ret_dict_key", 10)
    assert ret_dict is not None
    val = "{},{},{},{}".format(identifier, int_arg, str_arg, func_arg(), file_arg.name)
    with open(file_arg.name.replace(".txt", ".csv"), 'w') as f:
        f.write("some_info")

    f = open(file_arg.name.replace(".txt", ".csv"), 'rb')
    # f.close() # file must not be closed
    ret_dict = {"val": val,
                "results_file":f}
    return ret_dict


def ignore_func() -> {'arg3': int}:
    print("okok")

ignore_func()
import inspect
params = inspect.signature(ignore_func).parameters
print(params)