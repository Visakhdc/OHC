import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.CounterCashDenomination = publicWidget.Widget.extend({
    selector: '.cash_denomination_template',
    events: {
        'click #cash_transfer': '_TransferCash',
        'input .counts-input': '_onCountChange',
         'submit #cash_denomination_form': '_CashDenominationSubmit',
    },

    start: function () {
        this._super.apply(this, arguments);
        this._setCurrentDate();
        this.$('.counts-input').val('')
        this.$('.total-field').val('')
        this.$('#grand_total').val('0.00');

    },

    _setCurrentDate: function () {
        const today = new Date();
        const formattedDate = today.toISOString().split('T')[0];
        this.$('#date_field').val(formattedDate);
    },

    _onCountChange: function (ev) {
        const $input = $(ev.currentTarget);
        const count = parseInt($input.val()) || 0;
        const currency = parseInt($input.data('value')) || 0;
        const total = count * currency;

        const $row = $input.closest('tr');
        $row.find('.total-field').val(total.toFixed(2));

        this._updateGrandTotal();
    },

    _updateGrandTotal: function () {
        let grandTotal = 0;
        this.$('.total-field').each(function () {
            const val = parseFloat($(this).val()) || 0;
            grandTotal += val;
        });

        this.$('#grand_total').val(grandTotal.toFixed(2));
    },
    _TransferCash: function (ev) {
        const selectedCounterId = this.$('#counter').val();
        const from_counter = $('#from_counter').val();

        $('#from_counter').val(selectedCounterId);

    },
    _CashDenominationSubmit: function (ev) {
        ev.preventDefault();

        const cashInHand = parseFloat(this.$('#cash_in_hand').val()) || 0;
        const grandTotal = parseFloat(this.$('#grand_total').val()) || 0;

        console.log("Cash in Hand:", cashInHand, "Grand Total:", grandTotal);

        if (grandTotal !== cashInHand) {
            $('#validation-modal').modal('show');
            return;
        }

        this.$('#cash_denomination_form')[0].submit();
    },
});

