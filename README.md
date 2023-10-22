# ezXY

### A collection of scripts and custom nodes for [ComfyUI](https://github.com/comfyanonymous/ComfyUI).

## Features
- Automatic type-casting for most custom and native nodes.
- Compact math node
- List generation for iteration control
- Versitile XY plotter 

## Installation
Clone the repository to `custom_nodes` in your ComfyUI directory:
```
git clone https://github.com/GMapeSplat/ComfyUI_ezXY.git
```

## Scripts
**Automatic type-casting**
>Patches Comfy UI during runtime to allow integer and float slots to connect. Data types are cast automatically and clamped to the input slot's configured minimum and maximum values. Should work out of the box with most custom and native nodes. Might cause some compatibility issues, or break depending on your version of ComfyUI.
>
>Runtime patches do not modify any source files, but it is fairly brute force. Use at your own risk.
## Nodes

*ezXY Driver*
- Simple list generator for quickly and easily setting up XY plot workflows. If used with other list generators or math nodes, you can drive the primitive inputs of any node.
  
*Plot Images*
- Formats images into a single image grid. Use with ezXY Driver to set up XY plots. Capable of plotting images of different sizes together.
  
*ezMath*
- Compact math node.
  
*Iteration Driver*
- Simple integer list generator. Outputs a list of integers within the specified range.
  
*String to List*
- Takes a string of semi-colon seperated items and outputs them as a list of strings.
  
*Numbers to List*
- Takes a string of semi-colon seperated numbers and outputs them as a list. Supports in-line math and
  ranges.

*Item from List*
- Takes any list as an input and outputs a single specified item.
  
*Line to Console*
- Simple debugging node. Prints any input to the console.

## ToDo
- [ ] Labeler node
- [ ] List widget auto-populator? (for model loaders)
- [ ] Workflow examples
  