import { _t } from "@web/core/l10n/translation";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";

patch(ControlButtons.prototype, {
    async onClickGetWeight() {
        const order = this.pos.get_order();
        const selectedLine = order?.get_selected_orderline();

        if (!selectedLine) {
            this.notification.add(_t("Select an order line first."));
            return;
        }

        try {
            const response = await fetch("http://localhost:8000/api/weight");
            if (!response.ok) {
                throw new Error(`Weight service returned ${response.status}`);
            }

            const data = await response.json();
            const rawWeight = typeof data === "number" ? data : data?.weight;
            const weight = Number.parseFloat(rawWeight);

            if (!Number.isFinite(weight) || weight <= 0) {
                this.notification.add(_t("The scale did not return a valid weight."));
                return;
            }

            const result = selectedLine.set_quantity(weight, true);
            if (result) {
                this.notification.add(result.body || result.title);
                return;
            }

            this.notification.add(_t("Weight updated."), { type: "success" });
        } catch (error) {
            console.error("Failed to read weight", error);
            this.notification.add(_t("Could not read the weight from the scale service."));
        }
    },
});
