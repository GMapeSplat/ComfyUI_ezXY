import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";


const NUMBER_TYPES = ["FLOAT", "INT", "NUMBER"];


const ext = {
	name: "Comfy.ezXY",
	
	registerCustomNodes() {
        class ezNote {
            color=LGraphCanvas.node_colors.yellow.color;
            bgcolor=LGraphCanvas.node_colors.yellow.bgcolor;
            groupcolor = LGraphCanvas.node_colors.yellow.groupcolor;
            constructor() {
                if (!this.properties) {
                    this.properties = {};
                    this.properties.text="";
                }

                ComfyWidgets.STRING(this, "", ["", {default:this.properties.text, multiline: true}], app)

                this.serialize_widgets = true;
                this.isVirtualNode = true;

            }


        }

        // Load default visibility

        LiteGraph.registerNodeType(
            "MyNote",
            Object.assign(ezNote, {
                title_mode: LiteGraph.NORMAL_TITLE,
                title: "MyNote",
                collapsable: true,
            })
        );

        ezNote.category = "ezXY";
    },
	
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
		
		outputs.forEach( (output_type, index) => NUMBER_TYPES.includes(output_type) && (outputs[index] = NUMBER_TYPES.join(",")) );
	},
}

app.registerExtension(ext);