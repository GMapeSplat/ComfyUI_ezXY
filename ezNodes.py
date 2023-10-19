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

# %% editable=true slideshow={"slide_type": ""}
from PIL import Image
import math
import torch
import numpy as np
from typing import Any


# %% editable=true slideshow={"slide_type": ""} jupyter={"source_hidden": true}
class CatchImage:
    def __init__(self):
        self.imageList = list()
        
    @classmethod       
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "output_on_step": ("INT", {
                    "default": 1, 
                    "min": 1, #Minimum value
                    "max": 99, #Maximum value
                    "step": 1, #Slider's step
                    "display": "number" # Cosmetic only: display as "number" or "slider"
                }),
                "step": ("INT", {
                    "default": 0, 
                    "min": 1, #Minimum value
                    "max": 99, #Maximum value
                    "step": 1, #Slider's step
                    "display": "number" # Cosmetic only: display as "number" or "slider"
                }),
            }
        }
        
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGE",)
    
    FUNCTION = "appendImage"
    
    OUTPUT_NODE = False
    
    CATEGORY = "ezXY"
    
    def appendImage(self, images, output_on_step=1, step=0):
        for image in images:        
            self.imageList.append(image)
        
        if output_on_step != step+1:
            img = torch.zeros((16,4,4,16),dtype=torch.float32,)
            return img
        
        img = self.imageList
        self.imageList = list()
        return (img,)


# %% editable=true slideshow={"slide_type": ""} jupyter={"source_hidden": true}
class PlotImage:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "x_pos": ("INT", {
                    "default": 1, 
                    "min": 1, #Minimum value
                    "max": 999, #Maximum value
                    "step": 1, #Slider's step
                }),
                "y_pos": ("INT", {
                    "default": 1, 
                    "min": 1,
                    "max": 999,
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
        # grid might have more positions than input data
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
            # if largest image checked, update largest dimensions
            max_height = max( max_height, _height )
            max_width = max( max_width, _width )

        # blank image tensor
        null_image = torch.zeros(dim0, max_height, max_width, dim3)#fix this

        for i, image in enumerate(images):
            # remap position lists to the new grid's coordinates
            # (0,0) to (column_max, row_max)
            x, y = x_pos[i] - column_min, y_pos[i] - row_min

            # if image is smaller than largest image, pad it
            _height, _width = image_dims[i]
            if (_height < max_height or _width < max_width):
                # .detach() does somthing important I think
                _image = null_image.detach().clone()
                # slice top-left corner of blank image (0:_height, 0:_width)
                # then replace it with current image
                _image[:, :_height, :_width, :] = image
                image = _image
                
            # put each image in it's place
            # index 'i' is synchronised between position and image lists
            plot[y][x] = image

        for index, row in enumerate(plot):
            for jndex, item in enumerate(row):
                if type(item) != torch.Tensor:
                    row[jndex] = null_image
            plot[index] = torch.cat(row, 2)

        plot = torch.cat(plot, 1)
        return (plot,)


# %% editable=true slideshow={"slide_type": ""} jupyter={"source_hidden": true}
class XYIterator:
    def __init__(self):
        self.x_value = None
        self.y_value = None
        
        self.step = 1
        self.x_length = None
        self.y_length = None
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "x start": ("INT", {"default": 0, "min": 0, "max": 99, "step": 1}),
                "x stop": ("INT", {"default": 0, "min": 0, "max": 99, "step": 1}),
                "x step": ("INT", {"default": 0, "min": 0, "max": 99, "step": 1}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 99, "step": 1}),
            },
        }
    
    RETURN_TYPES = ("INT","INT","INT",)
    RETURN_NAMES = ("x", "y", "step",)
    
    FUNCTION = "iterate"
    
    CATEGORY = "ezXY"
    
    def iterate(self, x_start, x_stop, x_step, seed):
        if self.step == 1:
            self.x_value = x_start
            self.x_length = abs(x_stop - x_start) / x_step
            
        if self.x_value < x_stop:
            self.x_value += x_step
        
        self.step += 1
        
        return (self.x_value, seed, self.step)


# %% editable=true slideshow={"slide_type": ""} jupyter={"source_hidden": true}
class IntIterator:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "start_walk": ("INT", {"default": 0, "min": -9999, "max": 9999, "step": 1}),
                "end_walk": ("INT", {"default": 10, "min": -9999, "max": 9999, "step": 1}),
                "step_size": ("INT", {"default": 1, "min": 0, "max": 9999, "step": 1}),
                "steps_completed": ("INT", {"default": 0, "min": 0, "max": 99, "step": 1}),
            },
        }

    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("value", "cycles completed")

    FUNCTION = "iterate"

    CATEGORY = "ezXY"

    def iterate(self, start_walk, end_walk, step_size, steps_completed):
        walk_direction = end_walk - start_walk
        cycle_range = abs(walk_direction) + 1
        total_distance = steps_completed * step_size

        value = math.copysign(total_distance%cycle_range, walk_direction) + start_walk
        cycles_completed = math.floor(steps_completed*step_size / cycle_range)

        return(int(value), cycles_completed,)


# %% editable=true slideshow={"slide_type": ""} jupyter={"source_hidden": true}
class IterateAnything:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "steps_completed": ("INT", {"default": 0, "min": 0, "max": 99, "step": 1}),
            },
        }

    RETURN_TYPES = ("*", "INT")
    RETURN_NAMES = ("value", "cycles completed")

    FUNCTION = "iterate"

    CATEGORY = "ezXY"

    def iterate(self, steps_completed):
        return( 1, cycles_completed,)


# %% jupyter={"source_hidden": true}
# wildcard trick is taken from pythongossss's
class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False

any_type = AnyType("*")


# %% editable=true slideshow={"slide_type": ""} jupyter={"source_hidden": true}
class IterateRange:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "start_walk": ("FLOAT", {
                   "default": 0,
                   "min": -9999,
                    "max": 9999,
                    "step": 0.01,
                    "round": .001}),
                "end_walk": ("FLOAT", {
                    "default": 10,
                    "min": -9999,
                    "max": 9999,
                    "step": 0.01,
                    "round": .001}),
                "step_size": ("FLOAT", {
                    "default": 1,
                    "min": 0,
                    "max": 9999,
                    "step": 0.01,
                    "round": .001}),
                "steps_completed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 999,
                    "step": 1}),
            },
        }

    RETURN_TYPES = (any_type, any_type, "INT")
    RETURN_NAMES = ("value", "value (int)", "cycles completed")

    FUNCTION = "iterate"

    CATEGORY = "ezXY"

    
    def iterate(self, start_walk, end_walk, step_size, steps_completed):
        walk_direction = end_walk - start_walk
        cycle_distance = abs(walk_direction) + step_size
        total_distance = steps_completed * step_size

        value = math.copysign(total_distance%cycle_distance, walk_direction) + start_walk
        cycles_completed = math.floor(steps_completed*step_size / cycle_distance)

        return( value, int(value), cycles_completed,)


# %%
class IterationDriver:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "iterations": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 99,
                    "step": 1}),
            },
        }

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("Iteration",)

    OUTPUT_IS_LIST = (True,)

    FUNCTION = "iterate"

    CATEGORY = "ezXY"

    
    def iterate(self, iterations):
        return (list(range(0,iterations)),)


# %% editable=true slideshow={"slide_type": ""} jupyter={"source_hidden": true}
class IterateList:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "list": ("STRING", {
                    "multiline": True,
                    "default": "Semicolon seperated list, e.g. this;that;these"}),
                "steps_completed": ("INT", {"default": 0, "min": 0, "max": 99, "step": 1}),
            },
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("list item", "cycles completed")

    FUNCTION = "iterate"

    CATEGORY = "ezXY"

    
    def iterate(self, list, steps_completed):
        if list.endswith(";"):
            list = list.rstrip(";")
            
        input_list = list.split(";")
        input_length = len(input_list)

        list_item = input_list[steps_completed%input_length]
        cycles_completed = math.floor(steps_completed / input_length)
        
        return (list_item, cycles_completed,)


# %% jupyter={"source_hidden": true}
class Math:
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
                ],),
            },
            "optional":{
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
                value = a/b
            case  "modulo (a%b)":
                value = a%b
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
    RETURN_NAMES = ("x indicies", "y indicies", "current iteration",
                    "total iterations",)
    
    OUTPUT_IS_LIST = (True, True, True, False,)
    
    FUNCTION = "setupXY"
    CATEGORY = "ezXY"
    
    def setupXY(self, column_count, row_count):
        total_iterations =  column_count * row_count
        iterations = range(1, total_iterations+1)
        
        column_indicies, row_indicies = list(iterations), list(iterations)
        for i, _ in enumerate(iterations):
            row_indicies[i], column_indicies[i] = divmod(i, column_count)
            
        return (column_indicies, row_indicies, iterations, total_iterations)


# %% editable=true slideshow={"slide_type": ""} jupyter={"source_hidden": true}
class Line_to_Console:
    @classmethod
    def INPUT_TYPES(s):
        return{
            "required": {},
            "optional": {
                "to_console": ("*", {},)
            },
        }

    RETURN_TYPES = ()

    FUNCTION = "printToConsole"

    OUTPUT_NODE = True
    CATEGORY = "ezXY"

    def printToConsole(self,to_console):
        message = "----------\nLine to Console:\n----------\n\n"
        message = message + type(to_console).__name__ + ":   " + str(to_console)
        message += "\n----------"
        
        print(message)
        return(1,)


# %% editable=true slideshow={"slide_type": ""} jupyter={"source_hidden": true}
NODE_CLASS_MAPPINGS = {
    "IterateRange": IterateRange,
    "IterateList": IterateList,
    "IterationDriver": IterationDriver,
    "Math": Math,
    "ezXY_Driver": ezXY_Driver,
    "PlotImage": PlotImage,
    "Line_to_Console": Line_to_Console,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "IterateRange": "Iterate Range",
    "IterateList": "Iterate List",
    "IterationDriver": "Iteration Driver",
    "Math": "Math",
    "ezXY_Driver": "ezXY Driver",
    "PlotImage": "Plot Image",
    "Line_to_Console": "Line to Console",
}

# %%
