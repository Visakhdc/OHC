import { renderToElement } from "@web/core/utils/render";
import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";

export const PortalHomeCounterscashDenomination = publicWidget.Widget.extend({
    selector: '.o_website_cash_denomination_search',
    events: {
        'keyup .o_portal_cash_denomination_input': '_cash_denomination_search',
    },

    async start() {
        this._super(...arguments);
        await this._cash_denomination_search();
    },

    async _cash_denomination_search() {
        const cash_denomination_name = $('#cash_denomination_input').val() || "";
        const result = await rpc('/cash/denomination/search', { args: { 'rec': cash_denomination_name } });
        
        if (result && result.length) {
            $('.cash_denomination_results_table').html(renderToElement('CashDenominationSearch', { result }));
        } else {
            $('.cash_denomination_results_table').html("<p class='text-center'>No Records found</p>");
        }
    }
});

publicWidget.registry.PortalHomeCounterscashDenomination = PortalHomeCounterscashDenomination;
