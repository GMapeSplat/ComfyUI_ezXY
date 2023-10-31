import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";


const NUMBER_TYPES = ["FLOAT", "INT", "NUMBER"];
// This should equal something like "FLOAT,INT,NUMBER,STRING".
// That string can be used on the frontend slot types to allow an input or output to connect to multiple different types.
const VALID_OUTPUT_TYPES = [...NUMBER_TYPES, "STRING"].join(",");


const ext = {
	name: "Comfy.ezXY",
	
	nodeCreated(node, app) {
		// Fires every time a node is constructed
		// You can modify widgets/add handlers/etc here
		
		//console.log("ezExtension", node);
		
		// Loop through the recently constructed node's outputs
		// Replace every number type with litegraph's builtin multi-connection support (litegraph.core.js line 624?)
		/*
		for (const output of node.outputs) {
			const type = output.type;
			if (type === "FLOAT" || type === "INT" || type === "NUMBER") {
				output.type = "FLOAT,INT,NUMBER";
			}
		}*/
	},
	
	async beforeRegisterNodeDef(_, nodeData, app) {
		const outputs = nodeData.output;
		
		// I wrote this code, but I can't seem to remember how to read it.
		// I think it says "If a nodes output type is one of the types defined in 'NUMBER_TYPES', then do change the output type to NUMBER_TYPES.join(',')"
		// The && is just shorthand... probably.
		outputs.forEach( (output_type, index) => NUMBER_TYPES.includes(output_type) && (outputs[index] = VALID_OUTPUT_TYPES ));
	},
}

app.registerExtension(ext);