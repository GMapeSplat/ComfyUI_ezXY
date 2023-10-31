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

# %% editable=true slideshow={"slide_type": ""} jupyter={"outputs_hidden": true}
import math
import os
import torch
from pprint import pprint
from PIL import Image, ImageDraw, ImageFont
import numpy as np

EZXY_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(EZXY_PATH, "config.yaml")
FONT_PATH = os.path.join(EZXY_PATH, "font/FiraCode-Regular.otf")
# Bring in config
import yaml
#config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "config.yaml")
with open(CONFIG_PATH, 'r') as file:
    CONFIG = yaml.safe_load(file)


# %% jupyter={"source_hidden": true}
def wrapIndex(index, length):
    if length == 0:
        print("ezXY: Divide by zero error, returning 0.")
        return 0,0
        
    # Using modulo ensures the index won't go out of range, wrapping back to 0 instead
    # math.fmod returns more predictable results when index is negative
    index_mod = int(math.fmod(index, length))
    wraps = index//length
    return index_mod, wraps


# %%
def padImage(image, target_dimensions):
    dim0, dim1, dim2, dim3 = image.size()
    null_image = torch.zeros(dim0, target_dimensions[0], target_dimensions[1], dim3)

    height_offset = (target_dimensions[0] - dim1) // 2
    width_offset = (target_dimensions[1] - dim2) // 2
    
    null_image[:, height_offset:height_offset+dim1, width_offset:width_offset+dim2, :] = image
    image = null_image

    return image


# %% editable=true slideshow={"slide_type": ""}
class PlotImages:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "x_pos": ("INT", {
                    "default": 0, 
                    "min": -99, #Minimum value
                    "max": 99, #Maximum value
                    "step": 1, #Slider's step
                }),
                "y_pos": ("INT", {
                    "default": 0, 
                    "min": -99,
                    "max": 99,
                    "step": 1,
                }),
            },
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("Image Plot",)

    INPUT_IS_LIST = True
    
    FUNCTION = "plotXY"
    
    CATEGORY = "ezXY"
    
    def plotXY(self, images, x_pos, y_pos):
        # find the edges of grid
        column_min, column_max = min(x_pos), max(x_pos)
        row_min, row_max = min(y_pos), max(y_pos)
        
        # size of the grid
        # grid might have at least as many positions as input data
        column_range = range(column_min, column_max+1)
        row_range = range(row_min, row_max+1)

        # create the grid (2d list) of size row_range x column_range items
        # rows(y) at dimension 0, columns(x) take up dimension 1
        plot = list(row_range)
        for row,_ in enumerate(plot):
            plot[row] = list(column_range)

        # prepare variables for image size normalization
        dim0, max_height, max_width, dim3 = images[0].size()
        image_dims = list()
        for image in images:
            # check and store image size dimensions
            _, _height, _width, _ = image.size()
            image_dims.append([_height, _width])
            # if this is the largest image checked, update largest dimensions
            max_height = max( max_height, _height )
            max_width = max( max_width, _width )

        # Check if final plot will be too large (in pixels).
        # Change value in config.yaml if you want larger images
        pixels = max_height * len(plot) * max_width * len(plot[0])
        if pixels > CONFIG['max_image_size']:
            message = "ezXY: Plotted image too large\n"
            message = message + f"    Max pixels: {CONFIG['max_image_size']:,}\n"
            message = message + f"    Plot size : {pixels:,}\n"
            message = message + "    Returning single image."
            print(message)
            return([images[0]])

        # blank image tensor
        null_image = torch.zeros(dim0, max_height, max_width, dim3)

        for i, image in enumerate(images):
            # remap position lists to the new grid's coordinates
            # (0,0) to (column_max, row_max)
            x, y = x_pos[i] - column_min, y_pos[i] - row_min

            # if image is smaller than largest image, pad it
            _height, _width = image_dims[i]
            if (_height < max_height or _width < max_width):
                image = padImage(image, (max_height, max_width))
                
            # put each image in it's place
            # index 'i' is synchronised between position and image lists
            # so everything just kinda works out.
            plot[y][x] = image
            
        # I don't know a whole lot about tensors, but this works.
        # Start by iterating through the plot's rows, filling empty positions with blank images
        # Then concatonate the images horizontally, forming rows
        for index, row in enumerate(plot):
            for jndex, item in enumerate(row):
                if type(item) != torch.Tensor:
                    row[jndex] = null_image
            plot[index] = torch.cat(row, 2)

        # Finally, concatonate the rows together to form the finished plot
        plot = torch.cat(plot, 1)
        return (plot,)


# %% jupyter={"source_hidden": true}
class JoinImages:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_1": ("IMAGE",),
                "image_2": ("IMAGE",),
                "direction": (["Vertical", "Horizontal"],),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("Image",)
    
    FUNCTION = "join_images"
    
    CATEGORY = "ezXY"

    def join_images(self, image_1, image_2, direction):
        images = [image_1, image_2]

        # Set up indicies for comparisons and concatenation
        if direction == "Vertical":
            cat_dimension, joint_dimension = 1,2
        elif direction == "Horizontal":
            cat_dimension, joint_dimension = 2,1

        # Compare images to see if one needs to be padded
        # torch.cat requires that all but the target dimension have the same size
        # So we pad horizontally if we concatenate vertically.
        pad_this = -1
        if images[0].size()[joint_dimension] > images[1].size()[joint_dimension]:
            pad_this = 1
        elif images[0].size()[joint_dimension] < images[1].size()[joint_dimension]:
            pad_this = 0

        # If one of the images needs to be padded, do pad it.
        if pad_this != -1:
            # Sweet pop/insert pattern. Probably a sin.
            _image = images.pop(pad_this)
            
            pad_dims = None
            # Only pad an image on the joint axis
            if direction == "Vertical":
                pad_dims = (_image.size()[1], images[0].size()[2])
            elif direction == "Horizontal":
                pad_dims = (images[0].size()[1], _image.size()[2])

            _image = padImage(_image, pad_dims)
            # Put modified image back where we found it.
            images.insert(pad_this, _image)
            
        output = torch.cat(images, cat_dimension)
        return (output,)


# %% jupyter={"source_hidden": true}
class IterationDriver:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "iterations": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 999,
                    "step": 1}),
            },
        }

    RETURN_TYPES = ("INT", "INT",)
    RETURN_NAMES = ("Iteration", "Range")

    OUTPUT_IS_LIST = (True, False)

    FUNCTION = "iterate"

    CATEGORY = "ezXY"
    
    def iterate(self, iterations):
        return (list(range(0,iterations)), iterations,)


# %% jupyter={"source_hidden": true}
class NumbersToList:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "numbers": ("STRING", {
                    "multiline": True,
                    "default": "Semicolon separated list, e.g. 2;4;7.2\nRanges defined by start:stop:step, e.g. 0:10:1 or 0:10"}),
                "pick_index": ("INT", {"default": 0, "min": -999, "max": 999, "step": 1}),
            },
        }

    RETURN_TYPES = ("FLOAT", "FLOAT", "INT", "INT",)
    RETURN_NAMES = ("list", "picked number", "size", "wraps",)

    OUTPUT_IS_LIST = (True, False, False, False)

    FUNCTION = "pack"

    CATEGORY = "ezXY"
    
    def pack(self, numbers, pick_index):
        # Start by sanitizing input
        valid_chars = "0123456789.;:-+*/%"
        # For each character in numbers, check if it is valid. If yes, put into new string
        numbers = ''.join(char for char in numbers if char in valid_chars)
        # remove extra symobols from edges of string
        # string is allowed to start with . or -
        numbers = numbers.strip(";:+*/%")
        numbers = numbers.rstrip(".-")

        # Switch string to list so we can pop duplicates
        numbers = list(numbers)
        _dupe_test = numbers[0]
        i = 1
        while i < len(numbers):
            if (_dupe_test in ".;:-+*/%" and numbers[i] in ";:+*/%") or (_dupe_test == numbers[i] == "."):
                numbers.pop(i)
                continue
            _dupe_test = numbers[i]
            i+=1

        # Back to string so we can use split
        numbers = "".join(numbers)    
        chunks = numbers.split(";")
        for i, chunk in enumerate(chunks):
            if ":" in chunk:
                ranges = chunk.split(":")
                range_min = float(eval(ranges[0], {}))
                range_max = float(eval(ranges[1], {}))
                
                range_step = None                
                if len(ranges) > 2:
                    range_step = float(eval(ranges[2], {}))
                else:
                    range_step = 1

                chunks[i] = np.arange(range_min, range_max+1, range_step).tolist()

            else:
                chunks[i] = float(eval(chunk, {}))

        # If a range was found, chunks[i] will be a list rather than a number
        # We want a 0d array, so lets loop through everything and make use of .extend()
        output_list = []
        for chunk in chunks:
            if isinstance(chunk, list):
                output_list.extend(chunk)
            else:
                output_list.append(chunk)
            
        length = len(output_list)
        index_mod, wraps = wrapIndex(pick_index, length)
        
        return (output_list, output_list[index_mod], length, wraps)


# %% jupyter={"source_hidden": true}
class StringToList:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "string": ("STRING", {
                    "multiline": True,
                    "default": "Semicolon separated list, e.g. this;that;these"}),
                "pick_index": ("INT", {"default": 0, "min": -999, "max": 999, "step": 1}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ("list", "picked string", "size", "wraps")

    OUTPUT_IS_LIST = (True, False, False, False)

    FUNCTION = "pack"

    CATEGORY = "ezXY"

    def pack(self, string, pick_index):
        # sanitize input
        if string.endswith(";"):
            string = string.rstrip(";")
            
        string_as_list = string.split(";")
        length = len(string_as_list)

        index_mod, wraps = wrapIndex(pick_index, length)
        
        return (string_as_list, string_as_list[index_mod], length, wraps)


# %% editable=true slideshow={"slide_type": ""} jupyter={"source_hidden": true}
class ItemFromList:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input": ("",),
                "index": ("INT", {"default": 0, "min": -999, "max": 999, "step": 1}),
            },
        }

    RETURN_TYPES = ("", "INT", "INT",)
    RETURN_NAMES = ("list item", "size", "wraps",)

    INPUT_IS_LIST = True

    FUNCTION = "pick"

    CATEGORY = "ezXY"

    
    def pick(self, input, index):
        # Since INPUT_IS_LIST, arguments arn't pulled out of their list when sent to us
        index = index[0]
        length = len(input)

        index_mod, wraps = wrapIndex(index, length)
        list_item = input[index_mod]
        return (list_item, length, wraps,)


# %% jupyter={"source_hidden": true}
class StringToLabel:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input": ("STRING", {}),
                "font_size": ("INT", {"default": 45, "min": 1, "max": 200, "step": 1}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("Label",)

    FUNCTION = "createLabel"
    
    CATEGORY = "ezXY"

    def createLabel(self, input, font_size):
        font = ImageFont.truetype(FONT_PATH, font_size)
        
        # Fake image for size testing
        _image = Image.new("RGB", (1,1))
        _draw = ImageDraw.Draw(_image)
        _, _, length, height = _draw.textbbox((0,0), input, font)

        # Create the real image and its drawing obj
        label_image = Image.new("RGB", [length, int(height*1.1)])
        draw_obj = ImageDraw.Draw(label_image)

        # Draw the text. All the strange parameters are for centering the text.
        draw_obj.text((0,height//1.75), input, font=font, anchor='lm')

        # Converting to something that Comfy can understand.
        label_array = np.array(label_image, ndmin=4)
        label_array = torch.from_numpy(label_array)

        return (label_array,)


# %%
class ConcatenateString:
    @classmethod
    def INPUT_TYPES(s):
        return{
            "required": {
                "string_1": ("STRING", {"multiline": True,}),
                "separator": ("STRING", {}),
                "string_2": ("STRING", {"multiline": True,}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("Joined String",)

    FUNCTION = "concatenate_string"
    
    CATEGORY = "ezXY"

    def concatenate_string(self, string_1, separator, string_2):
        # To avoid accidentally adding numbers .join is used
        output = "".join([string_1, separator, string_2])
        return (output,)


# %%
class ezMath:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "operation": ([
                    "add (a+b+c)",
                    "subtract (a-b-c)",
                    "multiply add (a*b+c)",
                    "divide (a/b)",
                    "modulo (a%b)",
                    "maximum (abc)",
                    "minimum (abc)",
                    "floor (a)",
                    "ceiling (a)",
                    "round (a to b decimals)",],),
                "a": ("FLOAT", {
                   "default": 0,
                   "min": -9999,
                    "max": 9999,
                    "step": 0.01,
                    "round": .001}),
                "b": ("FLOAT", {
                   "default": 0,
                   "min": -9999,
                    "max": 9999,
                    "step": 0.01,
                    "round": .001}),
                "c": ("FLOAT", {
                   "default": 0,
                   "min": -9999,
                    "max": 9999,
                    "step": 0.01,
                    "round": .001}),
            },
        }

    RETURN_TYPES = ("FLOAT",)
    RETURN_NAMES = ("value",)

    FUNCTION = "operate"

    CATEGORY = "ezXY"

    
    def operate(self, operation, a = 0, b = 0, c = 0):
        value = None
        match operation:
            case "add (a+b+c)":
                value = a+b+c
            case "subtract (a-b-c)":
                value = a-b-c
            case "multiply add (a*b+c)":
                value = a*b+c
            case "divide (a/b)":
                if b != 0:
                    value = a/b
                else:
                    value = 0
                    print(f'Divide by zero error in {self}.\nReturning 0.')
            case  "modulo (a%b)":
                if b != 0:
                    value = math.fmod(a,b)
                else:
                    value = 0
                    print(f'Divide by zero error in {self}.\nReturning 0.')
            case "maximum (abc)":
                value = max(a,b,c)
            case "minimum (abc)":
                value = min(a,b,c)
            case "floor (a)":
                value = math.floor(a)
            case "ceiling (a)":
                value = math.ceil(a)
            case "round (a to b decimals)":
                value = round(a, int(b))
            case _:
                value = 0
        return (value,)


# %% jupyter={"source_hidden": true}
class ezXY_Driver:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "column_count": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 999,
                    "step": 1}),
                "row_count": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 999,
                    "step": 1}),
            },
        }

    RETURN_TYPES = ("INT", "INT", "INT", "INT")
    RETURN_NAMES = ("x indicies", "y indicies", "iteration",
                    "range",)
    
    OUTPUT_IS_LIST = (True, True, True, False,)
    
    FUNCTION = "setupXY"
    CATEGORY = "ezXY"
    
    def setupXY(self, column_count, row_count):
        total_iterations =  column_count * row_count
        # might need to change iterations... output inconsistent with iteration driver
        iterations = list(range(1, total_iterations+1))
        
        column_indicies, row_indicies = iterations.copy(), iterations.copy()
        for i, _ in enumerate(iterations):
            row_indicies[i], column_indicies[i] = divmod(i, column_count)
            
        return (column_indicies, row_indicies, iterations, total_iterations)


# %% editable=true slideshow={"slide_type": ""} jupyter={"source_hidden": true}
class LineToConsole:
    @classmethod
    def INPUT_TYPES(s):
        return{
            "required": {},
            "optional": {
                "to_console": ("*", {},),
                "table_depth": ("INT", {"default": 3, "min": 0, "max": 10, "step": 1,}),
            },
        }

    RETURN_TYPES = ()

    FUNCTION = "printToConsole"

    INPUT_IS_LIST = True
    
    OUTPUT_NODE = True
    CATEGORY = "ezXY"

    def printToConsole(self, to_console, table_depth):
        table_depth = table_depth[0]
        print("----------\nLine to Console:\n----------\n")        
        pprint(to_console, depth=table_depth, indent=4, sort_dicts=False)
        print("\n")
        return(1,)


# %% editable=true slideshow={"slide_type": ""} jupyter={"outputs_hidden": true}
NODE_CLASS_MAPPINGS = {
    "PlotImages": PlotImages,
    "JoinImages": JoinImages,
    "IterationDriver": IterationDriver,
    "StringToList": StringToList,
    "NumbersToList": NumbersToList,
    "ItemFromList": ItemFromList,
    "StringToLabel": StringToLabel,
    "ConcatenateString": ConcatenateString,
    "ezMath": ezMath,
    "ezXY_Driver": ezXY_Driver,
    "LineToConsole": LineToConsole,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PlotImages": "Plot Images",
    "JoinImages": "Join Images",
    "IterationDriver": "Iteration Driver",
    "StringToList": "String to List",
    "NumbersToList": "Numbers to List",
    "ItemFromList": "Item from List",
    "StringToLabel": "String to Label",
    "ConcatenateString": "Concatenate String",
    "ezMath": "ezMath",
    "ezXY_Driver": "ezXY Driver",
    "LineToConsole": "Line to Console",
}
