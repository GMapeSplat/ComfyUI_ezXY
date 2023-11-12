import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

const NUMBER_TYPES = ["FLOAT", "INT", "NUMBER"];

// This should equal something like "FLOAT,INT,NUMBER,STRING".
// That string can be used on the frontend slot types to allow an input or output to connect to multiple different types.
const VALID_OUTPUT_TYPES = [...NUMBER_TYPES, "STRING"].join(",");

// This widget exposes a dropdown menu's options.
// name should be the name of the input you're targeting in your python code.
// Can be used to select any number of options and order them however.
// Wasn't supposed to be this long.
class MultiSelectWidget
{
	constructor(node, name, opts, app)
	{
		this.name = name;
		this.node = node;
		// Quick runtime patch for serialization/configure purposes
		const old_onConfigure = node.onConfigure;
		node.onConfigure = function()
		{
			// Make sure to keep nodes original configure function
			const r = (old_onConfigure)? old_onConfigure.apply(this, arguments) : undefined;
			
			if (this.MultiSelectWidget_info)
			{
				const widget = this.widgets.find( w => w.type === "multiselect");
				widget.pullOptions(this.MultiSelectWidget_info);
			}
			return r;
		}
		//Same as above
		const old_onSerialize = node.onSerialize;
		node.onSerialize = function(info)
		{
			const r = (old_onSerialize)? old_onSerialize.apply(this, arguments) : undefined;
			info.MultiSelectWidget_info = this.MultiSelectWidget_info;
		}
		// LGraphNode.prototype.computeSize doesn't account for widget width for some reason.
		// Need to modify it's return value whenever it's called.
		const old_computeSize = node.computeSize;
		node.computeSize = function(out)
		{
			const r = (old_computeSize)? old_computeSize.apply(this, arguments) : undefined;
			const widget = this.widgets.find( w => w.type === "multiselect");
			return (r[0] && widget)? [ Math.max(r[0], widget.size[0] + 22), r[1] ] : undefined;
		}
		
	}
	
	type = "multiselect";
	size = [0, 0];
	optionListChanged = true;
	// Value ultimately used by our node.
	get value()
		{return this.selected.join(";")}
	// Don't really need this, but it conforms to Comfy's other widgets
	options =
	{
		values: [""],
	}
	// Convinient object for serialization.
	#multiSelecter =
	{
		optionList: [],
		selectedIndicies: [],
		selectedCount: 0
	}
	// Getters/Setters for multiSelecter
	get optionList()
		{return this.#multiSelecter.optionList}
	set optionList(ops)
	{
		this.#multiSelecter.optionList = [...ops];
		this.options.values = [...ops];
		this.#multiSelecter.selectedIndicies = [...ops].fill(null);
		this.#multiSelecter.selectedCount = 0;
		this.optionListChanged = true; // Flag for draw method
	}
	get selectedIndicies()
		{return this.#multiSelecter.selectedIndicies;}
	get selectedCount()
		{return this.#multiSelecter.selectedCount;}
	// Returns a list of only the selected items
	get selected()
	{
		const result = [];
		this.selectedIndicies.forEach( (elem,i) => (elem!==null) && (result[elem] = this.optionList[i]) );
		return result
	}
	// Returns a list of only the unselected items
	get unselected()
	{
		const result = [];
		this.selectedIndicies.forEach( (elem,i) => (elem===null) && result.push(this.optionList[i]) );
		return result
	}
	// Replace a null with the current count
	// This value is used to order the selected list by age
	selectOption(index)
	{
		this.selectedIndicies[index] = this.selectedCount;
		this.#multiSelecter.selectedCount += 1;
	}
	// Replace chosen index with null, decrement any values larger than index to fill in gaps
	deselectOption(index)
	{
		const selected = this.selectedIndicies.splice(index, 1, null);
		this.selectedIndicies.forEach( (elem,i,_this) => _this[i] = (elem > selected)? elem-1 : elem );
		
		this.#multiSelecter.selectedCount -= 1;
	}
	// These are for serializing the widget.
	// Push only needs to be called when making a new link.
	// Since it passes an object, it'll update automatically.
	pushOptions()
		{this.node.MultiSelectWidget_info = this.#multiSelecter;}
	pullOptions(info)
	{
		this.#multiSelecter = info;
		// Copy options list so it can't be chnaged via options.values
		this.options.values = [...this.#multiSelecter.optionList]
	}

    /** Called by `LGraphCanvas.drawNodeWidgets` */
    draw(ctx, node, width, poxY, height)
	{
		// Initialize ctx stuff
		ctx.font = "12px serif";
		ctx.textBaseline = "top";
		ctx.strokeStyle = "black";
		// Get a ton of variable set for positioning elements
		const MARGIN = 10;
		const item_count = Math.max(node.outputs.length, node.inputs.length) + node.widgets.length;
		// Need these on widget level for mouse
		this.y = ((item_count-1) * height) + MARGIN;
		this.line_height ??= ctx.measureText("M").width * 1.3;
		this.div_pos = this.selectedCount * this.line_height + this.y;
		this.div_height = 3
		
		// This sets the widget's size and in turn sets the node's minimum size.
		if (this.optionListChanged)
		{
			let longest = 0;
			this.optionList.forEach( option => longest = Math.max(ctx.measureText("00: "+option).width, longest) );
			this.size[0] = longest;
			this.size[1] = this.optionList.length * this.line_height + this.div_height;
			
			this.optionListChanged = false;
			node.size = node.computeSize();
			node.graph.setDirtyCanvas(true); // This forces a redraw so the node updates its size immediately.
		}
			
		// Background fill
		ctx.fillStyle = (node.color)? node.color : "#222";
		ctx.fillRect( MARGIN, this.y, width-20, this.size[1] );
		// Selected/Unselected Divider
		ctx.fillStyle = "gray";
		ctx.fillRect( MARGIN, this.div_pos, width-20, this.div_height );
		// Text
		ctx.fillStyle = "green";
		this.selected.forEach( (v,index) =>
		{
			const _line = index + ": " + v;
			ctx.strokeText(_line, MARGIN, this.y + this.line_height*index);
			ctx.fillText(_line, MARGIN, this.y + this.line_height*index);
		});
		ctx.fillStyle = "red";
		this.unselected.forEach( (v,index) =>
		{
			ctx.strokeText(v, MARGIN, this.div_pos + this.div_height + this.line_height*index);
			ctx.fillText(v, MARGIN, this.div_pos + this.div_height + this.line_height*index);
		});
	}

    mouse(event, pos, node)
	{
		if (event.click_time) //mouseup
		{
			if (pos[1] > this.y && pos[1] < this.div_pos ) // In Selected Box
			{
				
				if (this.selectedCount > 1)
				{
					const target_index = Math.floor( (pos[1]-this.y) / this.line_height );
					const index_of_value = this.selectedIndicies.indexOf(target_index);
					this.deselectOption(index_of_value);
				}
			}
			else if (pos[1] > this.div_pos + this.div_height) // In Unselected Box
			{
				if (this.selectedCount !== this.optionList.length)
				{
					const target_index = Math.floor( (pos[1]-this.div_pos-this.div_height) / this.line_height);
					const result = this.optionList.indexOf(this.unselected[target_index]);
					this.selectOption(result);
				}
			}
		}
		return false;
	}
    /** Called by `LGraphNode.computeSize` */
    computeSize(width) // returns [x, y]
	{
		return this.size;
	}
}

const ext = {
	name: "Comfy.ezXY",

	async beforeRegisterNodeDef(_, nodeData, app) {
		const outputs = nodeData.output;
		
		// I wrote this code, but I can't seem to remember how to read it.
		// I think it says "If a nodes output type is one of the types defined in 'NUMBER_TYPES', then do change the output type to NUMBER_TYPES.join(',')"
		// The && is just shorthand... probably.
		outputs.forEach( (output_type, index) => NUMBER_TYPES.includes(output_type) && (outputs[index] = VALID_OUTPUT_TYPES ));
	},
		
	nodeCreated(node, app) {
		// Fires every time a node is constructed
		// You can modify widgets/add handlers/etc here
		// When this is executed, we are still inside the constructor,
		// 	so node isn't an object until everything is finished executing.
		// We can still assign properties, though.
		
		// ItemFromDropdown handling
		if (node.getTitle() === "Item from Dropdown" )
		{
			// Unintrusively change the nodes output type to something useful
			// Hacks around the frontend's janky COMBO authentication, too.
			node.setOutputDataType(0, "COMBO,STRING");
			
			// Replace node's first input with a widget.
			// I think the only thing that connects an input with the backend is it's name.
			const input_name = node?.inputs[0]?.name;
			if (input_name)	node.removeInput(0);
			
			let opts; // Maybe will use this later
			const my_widget = new MultiSelectWidget(node, input_name, opts, app); // Custom widget
			node.addCustomWidget(my_widget);
			
			// Set up linking behaviors.
			//When attaching to a COMBO input, setup the widget.
			node.onConnectOutput = function(outputIndex, inputType, inputSlot, inputNode, inputIndex)
			{
				if (inputType !== "COMBO") return true;
				
				const input_options = inputNode?.widgets[inputIndex].options.values;
				my_widget.optionList = input_options;
				my_widget.selectOption(0);
				my_widget.pushOptions();
			}
			
			//////////////////////////////////////////
			// Proceed no further, inquisitive one, //
			//         lest thine eyes				//
			//    fall upon my shame and weep		//
			//////////////////////////////////////////
			/*
			// Set up an objectively terrible text display.
			node.onDrawForeground = function(ctx, graphcanvas)
			{
				if(this.flags.collapsed) return;
				ctx.save();
			  
				ctx.font = "12px serif";
				ctx.textBaseline = "top";
				ctx.strokeStyle = "black";
				
				line_height = !line_height? ctx.measureText("M").width * 1.2 : line_height;
				//const lineHeight = ctx.measureText("M").width * 1.2;
				//const lineHeight = LiteGraph.NODE_SLOT_HEIGHT;
				//const selected_height = (node.selected.length || 1) * lineHeight;
				//const unselected_height = (node.options.length || 1) * lineHeight;
				
				selected_height = (node?.selected.length || 1) * line_height;
				unselected_height = (node?.unselected.length || 0) * line_height;
				//const offset_y = 6;	// top margin
				//const offset_x = 5;	// left margin
				//ctx.fillText("Selected", 2, 5);
			
				ctx.fillStyle = (node.color)? node.color : "#222";
				ctx.fillRect(...selected_rect());
				ctx.fillRect(...unselected_rect());

				ctx.fillStyle = "green";
				if (Array.isArray(node.selected))
				{
					node.selected.forEach( (v,index) => 
					{
						const _line = index + ":" + node?.options[v];
						ctx.strokeText(_line, LEFT_MARGIN, TOP_MARGIN + line_height * index);
						ctx.fillText(_line, LEFT_MARGIN, TOP_MARGIN + line_height * index);
					});
				}

				ctx.fillStyle = "red";
				if (Array.isArray(node.unselected))
				{
					node.unselected.forEach( (v,index) =>
					{
						ctx.strokeText(node?.options[v], LEFT_MARGIN, TOP_MARGIN * 2 + selected_height + line_height * index);
						ctx.fillText(node?.options[v], LEFT_MARGIN, TOP_MARGIN * 2 + selected_height + line_height * index);
					});
				}

				ctx.restore();
			}
			
			node.onMouseUp = function( event, pos, graphcanvas )
			{
				// Double clicks only? Event might be getting caught somewhere else.
				const [x, y] = pos
				const [sel_left, sel_top, sel_right, sel_bot] = selected_rect();
				const [,un_top,,un_bot] = unselected_rect();
				
				if (x < sel_left || x > sel_right) return false; // Out of scope
				
				if (y > sel_top && y < sel_top + sel_bot ) // In Selected Box
				{
					if (node?.selected.length > 1)
					{
						const target_index = Math.floor( (y - sel_top) / line_height);
						const target_value = node?.selected.splice(target_index,1)[0];
						node?.unselected.splice(target_value, 0, target_value);
						node?.unselected.sort((a,b) => a-b);
					}
				}
				
				else if (y > un_top && y < un_top + un_bot ) // In Unselected Box
				{
					const target_index = Math.floor( (y - un_top) / line_height);
					node?.selected.push(node?.unselected.splice(target_index, 1)[0]);
				}
				
				my_widget.update();
				//return true; //return true is the event was used by your node, to block other behaviours
			}
			*/
		}
	},
}

app.registerExtension(ext);