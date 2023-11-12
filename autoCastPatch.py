# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% jupyter={"outputs_hidden": true}
import sys
import execution
import nodes

# Castable types recognized by ezXY stuff + dropdown handling
NUMBER_TYPES = ["FLOAT", "INT", "NUMBER", "COMBO"]

# %% jupyter={"outputs_hidden": true}
# monkey patch validate_inputs
# This could cause some compatability issues with other custom mods and scripts.
# Only adds a couple lines of code and a tab to the built-in function.
# There is probably a cooler way to do this, but I'm dumb and just want it to work.

_validate_inputs = execution.validate_inputs

def validate_inputs(prompt, item, validated):
    '''
    # uncomment this to restore normal functionality.
    return _validate_inputs(prompt, item, validated)
    '''
    unique_id = item
    if unique_id in validated:
        return validated[unique_id]

    inputs = prompt[unique_id]['inputs']
    class_type = prompt[unique_id]['class_type']
    obj_class = nodes.NODE_CLASS_MAPPINGS[class_type]

    class_inputs = obj_class.INPUT_TYPES()
    required_inputs = class_inputs['required']

    errors = []
    valid = True

    for x in required_inputs:
        if x not in inputs:
            error = {
                "type": "required_input_missing",
                "message": "Required input is missing",
                "details": f"{x}",
                "extra_info": {
                    "input_name": x
                }
            }
            errors.append(error)
            continue

        val = inputs[x]
        info = required_inputs[x]
        type_input = info[0]
        if isinstance(val, list):
            if len(val) != 2:
                error = {
                    "type": "bad_linked_input",
                    "message": "Bad linked input, must be a length-2 list of [node_id, slot_index]",
                    "details": f"{x}",
                    "extra_info": {
                        "input_name": x,
                        "input_config": info,
                        "received_value": val
                    }
                }
                errors.append(error)
                continue

            o_id = val[0]
            o_class_type = prompt[o_id]['class_type']
            r = nodes.NODE_CLASS_MAPPINGS[o_class_type].RETURN_TYPES
            
            # \/\/\/ Custom Verification Here \/\/\/
            # If either side of a link is expecting a type that isn't handled,
            # do run the function as normal, otherwise skip the type matching verification.
            if isinstance(type_input, list): type_input = "COMBO"
            if r[val[1]] not in NUMBER_TYPES or type_input not in [*NUMBER_TYPES, "STRING"]:
            # /\/\/\/\/\/\
                
                if r[val[1]] != type_input:
                    received_type = r[val[1]]
                    details = f"{x}, {received_type} != {type_input}"
                    error = {
                        "type": "return_type_mismatch",
                        "message": "Return type mismatch between linked nodes",
                        "details": details,
                        "extra_info": {
                            "input_name": x,
                            "input_config": info,
                            "received_type": received_type,
                            "linked_node": val
                        }
                    }
                    errors.append(error)
                    continue
            try:
                r = validate_inputs(prompt, o_id, validated)
                if r[0] is False:
                    # `r` will be set in `validated[o_id]` already
                    valid = False
                    continue
            except Exception as ex:
                typ, _, tb = sys.exc_info()
                valid = False
                exception_type = full_type_name(typ)
                reasons = [{
                    "type": "exception_during_inner_validation",
                    "message": "Exception when validating inner node",
                    "details": str(ex),
                    "extra_info": {
                        "input_name": x,
                        "input_config": info,
                        "exception_message": str(ex),
                        "exception_type": exception_type,
                        "traceback": traceback.format_tb(tb),
                        "linked_node": val
                    }
                }]
                validated[o_id] = (False, reasons, o_id)
                continue
        else:
            try:
                if type_input == "INT":
                    val = int(val)
                    inputs[x] = val
                if type_input == "FLOAT":
                    val = float(val)
                    inputs[x] = val
                if type_input == "STRING":
                    val = str(val)
                    inputs[x] = val
            except Exception as ex:
                error = {
                    "type": "invalid_input_type",
                    "message": f"Failed to convert an input value to a {type_input} value",
                    "details": f"{x}, {val}, {ex}",
                    "extra_info": {
                        "input_name": x,
                        "input_config": info,
                        "received_value": val,
                        "exception_message": str(ex)
                    }
                }
                errors.append(error)
                continue

            if len(info) > 1:
                if "min" in info[1] and val < info[1]["min"]:
                    error = {
                        "type": "value_smaller_than_min",
                        "message": "Value {} smaller than min of {}".format(val, info[1]["min"]),
                        "details": f"{x}",
                        "extra_info": {
                            "input_name": x,
                            "input_config": info,
                            "received_value": val,
                        }
                    }
                    errors.append(error)
                    continue
                if "max" in info[1] and val > info[1]["max"]:
                    error = {
                        "type": "value_bigger_than_max",
                        "message": "Value {} bigger than max of {}".format(val, info[1]["max"]),
                        "details": f"{x}",
                        "extra_info": {
                            "input_name": x,
                            "input_config": info,
                            "received_value": val,
                        }
                    }
                    errors.append(error)
                    continue

            if hasattr(obj_class, "VALIDATE_INPUTS"):
                
                # \/\/\/ added execution. to get_input_data \/\/\/
                input_data_all = execution.get_input_data(inputs, obj_class, unique_id)
                # /\/\/\ End cutom code /\/\/\
                
                #ret = obj_class.VALIDATE_INPUTS(**input_data_all)
                ret = map_node_over_list(obj_class, input_data_all, "VALIDATE_INPUTS")
                for i, r in enumerate(ret):
                    if r is not True:
                        details = f"{x}"
                        if r is not False:
                            details += f" - {str(r)}"

                        error = {
                            "type": "custom_validation_failed",
                            "message": "Custom validation failed for node",
                            "details": details,
                            "extra_info": {
                                "input_name": x,
                                "input_config": info,
                                "received_value": val,
                            }
                        }
                        errors.append(error)
                        continue
            else:
                if isinstance(type_input, list):
                    if val not in type_input:
                        input_config = info
                        list_info = ""

                        # Don't send back gigantic lists like if they're lots of
                        # scanned model filepaths
                        if len(type_input) > 20:
                            list_info = f"(list of length {len(type_input)})"
                            input_config = None
                        else:
                            list_info = str(type_input)

                        error = {
                            "type": "value_not_in_list",
                            "message": "Value not in list",
                            "details": f"{x}: '{val}' not in {list_info}",
                            "extra_info": {
                                "input_name": x,
                                "input_config": input_config,
                                "received_value": val,
                            }
                        }
                        errors.append(error)
                        continue

    if len(errors) > 0 or valid is not True:
        ret = (False, errors, unique_id)
    else:
        ret = (True, [], unique_id)

    validated[unique_id] = ret
    return ret

# Put the edited code back where we found it (kinda)
execution.validate_inputs = validate_inputs
print("validate_inputs() from execution.py patched by ezXY.")

# %%
# Monkey patch map_node_over_list.
# Modifies node function parameteres right before they are executed.
# Operations are type casting and range clamping.

_map_node_over_list = execution.map_node_over_list

def map_node_over_list(obj, input_data_all, func, allow_interrupt=False):
    cast_this = False

    # Gather necessary info about the current node
    node_inputs = dict()
    _info = obj.INPUT_TYPES()
    
    if 'required' in _info:
        node_inputs.update(_info['required'])
    if 'optional' in _info:
        node_inputs.update(_info['optional'])

    # node_inputs = {input_name: (input_type, {default: foo,})}
    for input_name, config in node_inputs.items():
        # for each input, typecast/clamp the incoming values.
        match config[0]:
            case "FLOAT" | "NUMBER":
                _nums = [float(value) for value in input_data_all[input_name]] 
                if 'min' in config[1]:
                    _nums = [max(nums_, config[1]['min']) for nums_ in _nums]
                if 'max' in config[1]:
                    _nums = [min(nums_, config[1]['max']) for nums_ in _nums]
                input_data_all[input_name] = _nums
                
            case "INT":
                _nums = [int(value) for value in input_data_all[input_name]]  
                if 'min' in config[1]:
                    _nums = [max(min_value, config[1]['min']) for min_value in _nums]
                if 'max' in config[1]:
                    _nums = [min(max_value, config[1]['max']) for max_value in _nums]
                input_data_all[input_name] = _nums

            case "STRING":
                _nums = [str(value) for value in input_data_all[input_name]]
                input_data_all[input_name] = _nums
                
    # Call original function using the sanitized input_data_all.
    return _map_node_over_list(obj, input_data_all, func, allow_interrupt)

execution.map_node_over_list = map_node_over_list
print('map_node_over_list() from execution.py patched by ezXY')
