/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class InvestmentDashboard extends Component {
    static template = "investment_club.Dashboard";
    static components = { Layout };

    setup() {
        this.action = useService("action");
        this.state = useState({
            stats: {},
            loading: true,
        });

        onWillStart(() => this.fetchStats());
    }

    get display() {
        return { controlPanel: {} };
    }

    async fetchStats() {
        this.state.loading = true;
        try {
            const data = await rpc("/investment/dashboard/stats");
            Object.assign(this.state, { stats: data, loading: false });
        } catch {
            this.state.loading = false;
        }
    }

    openModel(model, name) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: name || "",
            res_model: model,
            views: [[false, "list"], [false, "form"]],
            view_mode: "list,form",
            target: "current",
        });
    }

    openFilteredModel(model, name, domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: name || "",
            res_model: model,
            domain: domain,
            views: [[false, "list"], [false, "form"]],
            view_mode: "list,form",
            target: "current",
        });
    }

    formatAmount(amount, symbol, position) {
        if (position === "before") {
            return `${symbol} ${amount.toLocaleString()}`;
        }
        return `${amount.toLocaleString()} ${symbol}`;
    }
}

registry.category("actions").add("investment_dashboard", InvestmentDashboard);
