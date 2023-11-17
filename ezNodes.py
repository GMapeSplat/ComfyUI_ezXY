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
import cv2
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


# %% jupyter={"source_hidden": true}
"""
def forceCatImages(images, coordinates, force_all = False):
    x, y = coordinates
    # find the edges of grid
    column_min, column_max = min(x), max(x)
    row_min, row_max = min(y), max(y)
    
    # size of the grid
    # grid might have more positions than it has input data
    column_range = range(column_min, column_max+1)
    row_range = range(row_min, row_max+1)

    # Check which dimensions need to be padded before concatenation
    pad_dimensions = [0,0]
    if force_all:
        pad_dimensions = [1,1]
    else: 
        if len(column_range) > 1:
            pad_dimensions[0] += 1 
        if len(row_range) > 1:
            pad_dimensions[1] += 1

    # create the grid (2d list) of size row_range x column_range items
    # rows go first because that is the format Comy uses
    # values don't matter, they are only placeholders
    # rows(y) at dimension 0; columns(x) take up dimension 1
    plot = list(row_range)
    for i,_ in enumerate(plot):
        plot[i] = list(column_range)

    # Capture all image sizes and find the largest values
    max_height = max_width = 0
    image_sizes = []
    for image in images:
        _, _height, _width, _ = image.shape
        max_height = max(max_height, _height)
        max_width = max(max_width, _width)
        image_sizes.append({"height": _height, "width": _width})

    # Check if final plot will be too large (in pixels).
    # Change value in config.yaml if you want larger images
    pixels = max_height * len(plot) * max_width * len(plot[0])
    if pixels > CONFIG['max_image_size']:
        message = "ezXY: Plotted image too large\n"
        message = message + f"    Max pixels: {CONFIG['max_image_size']:,}\n"
        message = message + f"    Plot size(approx.) : {pixels:,}\n"
        message = message + "    Returning single image."
        print(message)
        return([images[0]])

    # Zero out max height or width if only padding along a single dimension.
    required_height, required_width = np.multiply([max_height,max_width], pad_dimensions)

    for i, dims in enumerate(image_sizes):
        # Pad undersized images
        if required_height > dims["height"] or required_width > dims["width"]:
            images[i] = padImage(images[i], (required_height, required_width))

        # remap position lists to the new grid's coordinates
        # desired variables look like (0,0) to (column_max, row_max)
        _x, _y = x[i] - column_min, y[i] - row_min
        
        # put each image in it's place
        # index 'i' is synchronised between position, image, and dim lists
        # so everything just kinda works out.
        plot[_y][_x] = images[i]


    # I don't know a whole lot about tensors, but this works.
    # Start by iterating through the plot's rows, filling empty positions with blank images
    # Then concatonate the images horizontally, forming rows
    null_image = torch.zeros(1, max_height, max_width, 3)
    for i, row in enumerate(plot):
        for j, item in enumerate(row):
            if type(item) != torch.Tensor:
                row[j] = null_image
        plot[i] = torch.cat(row, 2)

    # Finally, concatonate the rows together to form the finished plot
    plot = torch.cat(plot, 1)
    return plot
    """


# %% jupyter={"source_hidden": true}
def padImage(image, target_dimensions):
    dim0, dim1, dim2, dim3 = image.size()
    _height = max(dim1, target_dimensions[0])
    _width = max(dim2, target_dimensions[1])

    # Blank image of the minimum size
    _image = torch.zeros(dim0, _height, _width, dim3)

    top_pad = (_height - dim1) // 2
    bottom_pad = top_pad + dim1
    
    left_pad = (_width - dim2) // 2
    right_pad = left_pad + dim2
    
    # Very cool image splicing pattern
    # Replaces the center of the blank image with the image from params
    _image[:, top_pad:bottom_pad, left_pad:right_pad, :] = image
    
    return _image


# %% editable=true slideshow={"slide_type": ""} jupyter={"source_hidden": true}
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
    
    CATEGORY = "ezXY/image"
    
    def plotXY(self, images, x_pos, y_pos, force_all = False):
        # make sure we have enough x and y positions
        # if not, repeat the last entry
        if len(x_pos) < len(images):
            x_pos.extend( [x_pos[-1]] * (len(images)-len(x_pos)) );
        if len(y_pos) < len(images):
            y_pos.extend( [y_pos[-1]] * (len(images)-len(y_pos)) );
        
        # find the edges of grid
        column_min, column_max = min(x_pos), max(x_pos)
        row_min, row_max = min(y_pos), max(y_pos)
        
        # size of the grid
        # grid might have more positions than it has input data
        column_length = len(range(column_min, column_max+1))
        row_length = len(range(row_min, row_max+1))
    
        # Check which dimensions need to be padded before concatenation
        pad_dimensions = [0,0]
        if force_all:
            pad_dimensions = [1,1]
        else: 
            if column_length > 1:
                pad_dimensions[0] += 1 
            if row_length > 1:
                pad_dimensions[1] += 1
    
        # create the grid (2d list) of size row_range x column_range items
        # Pretty sweet pattern
        plot = [ [None] * column_length for i in range(row_length) ]
    
        # Capture all image sizes and find the largest values
        max_height = max_width = 0
        image_sizes = []
        for image in images:
            _, _height, _width, _ = image.shape
            max_height = max(max_height, _height)
            max_width = max(max_width, _width)
            image_sizes.append({"height": _height, "width": _width})
    
        # Check if final plot will be too large (in pixels).
        # Change value in config.yaml if you want larger images
        pixels = max_height * len(plot) * max_width * len(plot[0])
        if pixels > CONFIG['max_image_size']:
            message = "ezXY: Plotted image too large\n"
            message = message + f"    Max pixels: {CONFIG['max_image_size']:,}\n"
            message = message + f"    Plot size(approx.) : {pixels:,}\n"
            message = message + "    Returning single image."
            print(message)
            return([images[0]])
    
        # Zero out max height or width if only padding along a single dimension.
        required_height, required_width = np.multiply([max_height,max_width], pad_dimensions)
    
        for i, dims in enumerate(image_sizes):
            # Pad undersized images
            if required_height > dims["height"] or required_width > dims["width"]:
                images[i] = padImage(images[i], (required_height, required_width))
    
            # remap position lists to the new grid's coordinates
            # desired variables look like (0,0) to (column_max, row_max)
            _x, _y = x_pos[i] - column_min, y_pos[i] - row_min
            
            # put each image in it's place
            # index 'i' is synchronised between position, image, and dim lists
            # so everything just kinda works out.
            plot[_y][_x] = images[i]
    
        # I don't know a whole lot about tensors, but this works.
        # Start by iterating through the plot's rows, filling empty positions with blank images
        # Then concatonate the images horizontally, forming rows
        null_image = torch.zeros(1, max_height, max_width, 3)
        for i, row in enumerate(plot):
            for j, item in enumerate(row):
                if not torch.is_tensor(item):
                    row[j] = null_image
            plot[i] = torch.cat(row, 2)
    
        # Finally, concatonate the rows together to form the finished plot
        plot = torch.cat(plot, 1)
        return (plot,)


# %%
class JoinImages():
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
    
    CATEGORY = "ezXY/image"

    def join_images(self, image_1, image_2, direction):
        images = [image_1, image_2]
        
        x = y = None
        if direction == "Vertical":
            x = (0, 0)
            y = (0, 1)
        elif direction == "Horizontal":
            x = (0, 1)
            y = (0, 0)

        plotter = PlotImages()

        return plotter.plotXY(images, x, y, False)


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

    CATEGORY = "ezXY/list generation"
    
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
                    "placeholder": "Semicolon separated list, e.g. 2;4;7.2\nRanges defined by start:stop:step, e.g. 0:10:1 or 0:10"}),
            },
        }

    RETURN_TYPES = ("FLOAT", "INT",)
    RETURN_NAMES = ("list", "size",)

    OUTPUT_IS_LIST = (True, False,)

    FUNCTION = "numbersToList"

    CATEGORY = "ezXY/list generation"
    
    def numbersToList(self, numbers):
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
        
        return (output_list, length,)


# %%
class StringsToList:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "string": ("STRING", {
                    "multiline": True,
                    "placeholder": "Semicolon separated list, e.g. this;that;these"}),
            },
        }

    RETURN_TYPES = ("STRING", "INT",)
    RETURN_NAMES = ("list", "size",)

    OUTPUT_IS_LIST = (True, False,)

    FUNCTION = "pack"

    CATEGORY = "ezXY/list generation"

    def pack(self, string,):
        # sanitize input
        if string.endswith(";"):
            string = string.rstrip(";")
            
        string_as_list = string.split(";")
        length = len(string_as_list)

        return (string_as_list, length,)


# %% editable=true slideshow={"slide_type": ""} jupyter={"source_hidden": true}
class NumberFromList:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "list_input": ("FLOAT", {"forceInput":True},),
                "index": ("INT", {"default": 0, "min": -999, "max": 999, "step": 1}),
            },
        }

    RETURN_TYPES = ("FLOAT", "INT", "INT",)
    RETURN_NAMES = ("list item", "size", "wraps",)

    INPUT_IS_LIST = True
    OUTPUT_IS_LIST = (True, False, True)

    FUNCTION = "pick"

    CATEGORY = "ezXY/utility"
    
    def pick(self, list_input, index):
        length = len(list_input)

        wraps_list, item_list = [],[]
        for i in index:
            index_mod, wraps = wrapIndex(i, length)
            wraps_list.append(wraps)
            item_list.append(list_input[index_mod])
            
        return (item_list, length, wraps_list,)


# %% editable=true slideshow={"slide_type": ""} jupyter={"source_hidden": true}
class StringFromList:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "list_input": ("STRING", {"forceInput":True},),
                "index": ("INT", {"default": 0, "min": -999, "max": 999, "step": 1}),
            },
        }

    RETURN_TYPES = ("STRING", "INT", "INT",)
    RETURN_NAMES = ("list item", "size", "wraps",)

    INPUT_IS_LIST = True
    OUTPUT_IS_LIST = (True, False, True)

    FUNCTION = "pick"

    CATEGORY = "ezXY/utility"
    
    def pick(self, list_input, index):
        length = len(list_input)

        wraps_list, item_list = [],[]
        for i in index:
            index_mod, wraps = wrapIndex(i, length)
            wraps_list.append(wraps)
            item_list.append(list_input[index_mod])
            
        return (item_list, length, wraps_list,)


# %%
class ItemFromDropdown:
    @classmethod
    def INPUT_TYPES(s):
        return{
            "required": {
                "options": ("multiselect", {}),
                "index": ("INT",
                          {"default": 0,
                           "min": -999,
                           "max": 999,
                           "step": 1,
                           "defaultInput": True,
                          }),
            },
        }

    RETURN_TYPES = ("COMBO", "INT", "INT",)
    RETURN_NAMES = ("COMBO", "length", "wraps",)

    FUNCTION = "selectOption"

    CATEGORY = "ezXY/utility"

    def selectOption(self, options, index):
        # Janky, but I don't want to rewrite any code
        # Call functions from other nodes and just deal with their awkward inputs/outputs
        options_string, _ = StringsToList.pack(None, options)
        item_list, length, wraps_list = StringFromList.pick(None, options_string, [index])
        
        return (item_list[0], length, wraps_list[0])


# %% jupyter={"source_hidden": true}
class StringToLabel:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "input": ("STRING", {}),
                "font_size": ("INT", {"default": 45, "min": 1, "max": 200, "step": 1}),
                "clockwise_rotation": ([0, 90, 180, 270], {}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("Label",)

    FUNCTION = "createLabel"
    
    CATEGORY = "ezXY/image"

    def createLabel(self, input, font_size, clockwise_rotation):
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

        if clockwise_rotation:
            label_array = torch.rot90(label_array, -1*clockwise_rotation//90, [1,2])

        return (label_array,)


# %% jupyter={"source_hidden": true}
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
    
    CATEGORY = "ezXY/utility"

    def concatenate_string(self, string_1, separator, string_2):
        # To avoid accidentally adding numbers .join is used
        output = "".join([string_1, separator, string_2])
        return (output,)


# %% jupyter={"source_hidden": true}
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


# %% jupyter={"source_hidden": true}
class ezXY_AssemblePlot:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "x_labels": ("IMAGE",),
                "y_labels": ("IMAGE",),
            },
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("Plot",)
    
    INPUT_IS_LIST = True
    
    FUNCTION = "assemble_plot"
    CATEGORY = "ezXY"

    def assemble_plot(self, images, x_labels, y_labels):
        image_count = len(images)
        row_length = len(x_labels)
        column_length = len(y_labels)

        # Throw an error message if you have too many/few images
        if image_count != (row_length * column_length):
            print("Labels/Images don't add up!")
            return images

        # Figure grid coordinates for images
        x, y, = [], []
        for i in range(image_count):
            _y, _x = divmod(i, row_length)
            x.append(_x), y.append(_y)
        
        plotter = PlotImages()
        _plot = plotter.plotXY(images, x, y, True)[0]
        
        _, plot_height, plot_width, _ = _plot.shape
        # Calculate the maximum length for the labels
        max_x_label_length = max( plot_width // row_length, x_labels[0].shape[2] )
        max_y_label_length = max( plot_height // column_length, y_labels[0].shape[2] )

        # Pad first labels to their maximum size.
        # Once joined, this will ensure all labels are at least of length max_length
        x_labels[0] = padImage(x_labels[0], [x_labels[0].shape[1], max_x_label_length])
        y_labels[0] = padImage(y_labels[0], [y_labels[0].shape[1], max_y_label_length])

        # Set up positions for labels
        # Only Horizontal for now
        x_label_positions = [ list(range(row_length)), [0]*row_length ]
        y_label_positions = [ list(range(column_length)), [0]*column_length ]

        _x = plotter.plotXY(x_labels, x_label_positions[0], x_label_positions[1], True)[0]
        y_labels.reverse()
        _y = plotter.plotXY(y_labels, y_label_positions[0], y_label_positions[1], True)[0]
        _y = torch.rot90(_y, 1, [1,2])

        # Check lengths of joined labels
        _, x_height, x_width, _ = _x.shape
        _, y_height, y_width, _ = _y.shape

        # If our labels end up oversized, scale them back.
        # A lot of conversions. Kinda sucks but I don't know what to do about it.
        if x_width > plot_width:
            _x = _x.numpy()
            _x = cv2.resize(_x[0], [plot_width, x_height])
            _x = np.array(_x, ndmin=4 )
            _x = torch.from_numpy(_x)
        if y_height > plot_height:
            _y = _y.numpy()
            _y = cv2.resize(_y[0], [y_width, plot_height])
            _y = np.array(_y, ndmin=4 )
            _y = torch.from_numpy(_y)

        # Slap on the x labels
        _plot = torch.cat([_x, _plot], 1)
        # The Y labels need a blank corner
        corner = torch.zeros(1,x_height, y_width,3)
        _y = torch.cat([corner,_y], 1)
        # Finish the job
        plot = torch.cat([_y, _plot], 2)

        return (plot,)


# %% editable=true slideshow={"slide_type": ""} jupyter={"source_hidden": true}
class LineToConsole:
    @classmethod
    def INPUT_TYPES(s):
        return{
            "required": {},
            "optional": {
                "to_console": ("*", {},),
                "table_depth": ("INT", {"default": 3, "min": 1, "max": 10, "step": 1,}),
            },
        }

    RETURN_TYPES = ()

    FUNCTION = "printToConsole"

    INPUT_IS_LIST = True
    
    OUTPUT_NODE = True
    CATEGORY = "ezXY/debug"

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
    "StringsToList": StringsToList,
    "NumbersToList": NumbersToList,
    "StringFromList": StringFromList,
    "NumberFromList": NumberFromList,
    "StringToLabel": StringToLabel,
    "ConcatenateString": ConcatenateString,
    "ezMath": ezMath,
    "ezXY_Driver": ezXY_Driver,
    "ezXY_AssemblePlot": ezXY_AssemblePlot,
    "LineToConsole": LineToConsole,
    "ItemFromDropdown": ItemFromDropdown,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PlotImages": "Plot Images",
    "JoinImages": "Join Images",
    "IterationDriver": "Iteration Driver",
    "NumbersToList": "Numbers to List",
    "StringsToList": "Strings to List",
    "NumberFromList": "Number from List",
    "StringFromList": "String from List",
    "StringToLabel": "String to Label",
    "ConcatenateString": "Concatenate String",
    "ezMath": "ezMath",
    "ezXY_Driver": "ezXY Driver",
    "ezXY_AssemblePlot": "ezXY Assemble Plot",
    "LineToConsole": "Line to Console",
    "ItemFromDropdown": "Item from Dropdown",
}
