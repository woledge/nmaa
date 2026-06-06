/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import { useService } from "@web/core/utils/hooks";

patch(ClosePosPopup.prototype, {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
    },

    async printCashierHandover() {
        try {
            await this.report.doAction(
                "pos_cashier_handover.action_report_cashier_handover",
                [this.pos.session.id]
            );
        } catch (error) {
            this.notification.add("حدث خطأ أثناء طباعة التقرير", { type: "danger" });
            console.error("Cashier Handover Print Error:", error);
        }
    },
});
