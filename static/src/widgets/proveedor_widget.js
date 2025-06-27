/** @odoo-module **/
import { Many2OneField, many2OneField } from "@web/views/fields/many2one/many2one_field";
import { usePopover } from "@web/core/popover/popover_hook";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

class ProveedorInfoPopover extends Component {
    setup() {
        this.actionService = useService("action");
    }
    openPartnerForm() {
        const { partnerId } = this.props;
        if (partnerId) {
            this.actionService.doAction({
                type: 'ir.actions.act_window',
                res_model: 'res.partner',
                res_id: partnerId,
                views: [[false, 'form']]
            });
            if (this.props.close) {
                this.props.close(); // Cierra el popover al abrir el formulario
            } // Cierra el popover al abrir el formulario
        }
    }
}

ProveedorInfoPopover.template = "ingreso_tropas.ProveedorInfoPopover";
ProveedorInfoPopover.props = {
    partnerId: { type: Number, optional: true },
    partnerData: { type: Object, optional: true },
    partnerName: {type:String,optional:true},
    close: { type: Function, optional: true }, // Añade esta línea
};

class Many2OneWithInfoField extends Many2OneField {
    setup() {
        super.setup();
        this.popover = usePopover(ProveedorInfoPopover);
        this.orm = useService("orm");
    }

    get hasInfoButton() {
        return !!this.value && !this.state.isFloating;
    }

    showInfoPopup(ev) {
        if (!this.value) return;
        
        const partnerId = this.value[0]; // ID del proveedor
        const partnerName = this.value[1]; // Nombre del proveedor
        // Accedemos a los campos relacionados desde this.record.data
        const partnerData = {
            name: partnerName,
            street: this.props.record.data.street || "N/A",
            city:  this.props.record.data.city || "N/A",
            cuit:  this.props.record.data.cuit || "N/A",
            email:  this.props.record.data.email || "N/A"
        };
        console.log(this.props.record.data)
        console.log(partnerData)
        this.popover.open(ev.currentTarget, {
            partnerId: partnerId,
            partnerData: partnerData,
            partnerName: partnerName,
        });
        
    }
    hideInfoPopup() {
        this.popover.close();
        
    }

    
}

Many2OneWithInfoField.template = "ingreso_tropas.Many2OneWithInfoField";

export const many2OneWithInfoField = {
    ...many2OneField,
    component: Many2OneWithInfoField,
};

registry.category("fields").add("many2one_with_info", many2OneWithInfoField);