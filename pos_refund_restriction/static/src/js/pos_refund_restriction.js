/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { parseFloat } from "@web/views/fields/parsers";

const UNAUTHORIZED_MSG = _t(
    "You do not have permission to process refunds. Please contact your POS Administrator."
);

patch(TicketScreen.prototype, {
    getHasItemsToRefund() {
        if (this.pos.get_cashier()._role !== "manager") {
            return false;
        }
        return super.getHasItemsToRefund();
    },
    _onUpdateSelectedOrderline(event) {
        if (this.pos.get_cashier()._role !== "manager") {
            this.numberBuffer.reset();
            this.dialog.add(AlertDialog, {
                title: _t("Access Denied"),
                body: UNAUTHORIZED_MSG,
            });
            return;
        }
        return super._onUpdateSelectedOrderline(event);
    },
    async onDoRefund() {
        if (this.pos.get_cashier()._role !== "manager") {
            this.dialog.add(AlertDialog, {
                title: _t("Access Denied"),
                body: UNAUTHORIZED_MSG,
            });
            return;
        }
        return super.onDoRefund();
    },
});

patch(PosOrderline.prototype, {
    set_quantity(quantity, keep_price) {
        const quant = typeof quantity === "number" ? quantity : parseFloat("" + (quantity || 0));
        if (quant < 0) {
            return {
                title: _t("Access Denied"),
                body: UNAUTHORIZED_MSG,
            };
        }
        return super.set_quantity(quantity, keep_price);
    },
});
