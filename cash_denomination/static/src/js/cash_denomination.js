import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.CounterCashDenomination = publicWidget.Widget.extend({
    selector: '.cash_denomination_template',
    events: {
        'click #cash_transfer': '_TransferCash',
        'click #petty_cash_btn': '_OpenPettyCashModal',
        'input .petty-counts-input': '_onPettyCountChange',
        'click #submit_petty_cash': '_SubmitPettyCash',
        'input .counts-input': '_onCountChange',
        'submit #cash_denomination_form': '_CashDenominationSubmit',

    },

    start: function () {
        this._super.apply(this, arguments);
        this._setCurrentDate();
        this.$('.counts-input').val('')
        this.$('.total-field').val('')
        this.$('#grand_total').val('0.00');
        this.$('.petty-counts-input').val('');
        this.$('.petty-total-field').val('');
        this.$('#petty_grand_total').val('0.00');
        this.$('#total_cash_field').val('0.00');
        this.$('#cash_in_hand').val('0.00');
        this.$('#petty_cash_total_field').val('0.00');

        const alreadySubmitted = this._checkAlreadySubmitted();
        if (alreadySubmitted) return;

        this._checkAlreadySubmitted();
        this._checkSameCounterError();
        this._checkInsufficientCash();
        this._checkTransferSuccess();
        this._checkPettySuccess();

        this._setupCounterUserLink();

        const defaultCounter = this.$('#counter').val();
        if (defaultCounter) {
            this._fetchPaymentAmountByCounter(defaultCounter);
        }

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
        ev.preventDefault();
        ev.stopPropagation();

        const selectedCounterId = this.$('#counter').val();
        const CashInHand = parseFloat(this.$('#cash_in_hand').val()) || 0;
        const LoggedUser = this.$('#person').val();

        if (CashInHand <= 0) {
            $('#no-cash-modal').modal('show');
            return;
        }

        $('#from_counter').val(selectedCounterId);
        $('#transfer_cash_in_hand').val(CashInHand);
        $('#logged_user').val(LoggedUser);

        $('#to_counter option').each(function () {
            const value = $(this).val();
            if (value == selectedCounterId) {
                $(this).hide();
            } else {
                $(this).show();
            }
        });

        $('#transfer-modal').modal('show');
    },

    _OpenPettyCashModal: function (ev) {
        ev.preventDefault();

        const selectedCounterId = this.$('#counter').val();
        const LoggedUser = this.$('#person').val();
        const CreatedDate = this.$('#date_field').val();
        const cashInHand = parseFloat(this.$('#cash_in_hand').val()) || 0;

        if (cashInHand <= 0) {
            $('#no-cash-modal-petty').modal('show');
            return;
        }
        else {
            $('#petty_cash_modal').modal('show');
        }
        if (selectedCounterId) {
            this._fetchPettyUsersByCounter(selectedCounterId);
        }

        $('#from_selected_counter').val(selectedCounterId);
        $('#logged_user').val(LoggedUser);
        $('#created_date').val(CreatedDate);
    },

    _onPettyCountChange: function (ev) {
        const $input = $(ev.currentTarget);
        const count = parseInt($input.val()) || 0;
        const currency = parseInt($input.data('value')) || 0;
        const total = count * currency;

        const $row = $input.closest('tr');
        $row.find('.petty-total-field').val(total.toFixed(2));

        this._updatePettyGrandTotal();
    },
    _updatePettyGrandTotal: function () {
        let grandTotal = 0;
        this.$('.petty-total-field').each(function () {
            const val = parseFloat($(this).val()) || 0;
            grandTotal += val;
        });
        this.$('#petty_grand_total').val(grandTotal.toFixed(2));
    },

    _CashDenominationSubmit: function (ev) {
        ev.preventDefault();
        const cashInHand = parseFloat(this.$('#cash_in_hand').val()) || 0;
        const grandTotal = parseFloat(this.$('#grand_total').val()) || 0;

        if (grandTotal === 0) {
            $('#no-count-modal').modal('show');
            return;
        }

        if (grandTotal !== cashInHand) {
            $('#validation-modal').modal('show');
            return;
        }

        $('#success-modal').modal('show');

        $('#success-modal').one('hidden.bs.modal', () => {
            this.$('#cash_denomination_form')[0].submit();
        });
    },
    _checkTransferSuccess: function () {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('transfer_success') === '1') {
            $('#transfer-success-modal').modal('show');

            const newUrl = window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
        }
    },

    _checkSameCounterError: function () {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('same_counter_error') === '1') {
            $('#same-counter-modal').modal('show');

            const newUrl = window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
        }
    },

    _checkInsufficientCash: function () {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('insufficient_cash') === '1') {
            $('#insufficient-cash-modal').modal('show');
            const newUrl = window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
        }
    },

    _setupCounterUserLink: function () {
        const self = this;

        document.addEventListener('shown.bs.modal', function (event) {
            if (event.target.id === 'transfer-modal') {
                const counterSelect = document.querySelector('#to_counter');
                const selectedCounterId = counterSelect?.value;
                if (selectedCounterId) {
                    self._fetchUsersByCounter(selectedCounterId);
                }
            }
        });

        document.querySelector('#to_counter')?.addEventListener('change', function (ev) {
            const counterId = ev.target.value;
            if (counterId) {
                self._fetchUsersByCounter(counterId);
            }
        });

        document.querySelector('#counter')?.addEventListener('change', function (ev) {
            const counterId = ev.target.value;
            if (counterId) {
                self._fetchPaymentAmountByCounter(counterId);
                self._checkPettyCashByCounter(counterId);
            }
        });
    },

    _fetchUsersByCounter: function (counterId) {
        const self = this;
        const loggedUserName = this.$('#person').val();

        rpc('/get/users/by/counter', { counter_id: counterId })
            .then(function (result) {
                const userSelect = document.querySelector('#transfer_to_user');
                userSelect.innerHTML = '';

                if (result && result.users && result.users.length > 0) {
                    const filteredUsers = result.users.filter(user => user.name !== loggedUserName);

                    if (filteredUsers.length > 0) {
                        filteredUsers.forEach(user => {
                            const option = document.createElement('option');
                            option.value = user.id;
                            option.textContent = user.name;
                            userSelect.appendChild(option);
                        });
                    } else {
                        const option = document.createElement('option');
                        option.textContent = 'No users found';
                        option.disabled = true;
                        option.selected = true;
                        userSelect.appendChild(option);
                    }
                } else {
                    const option = document.createElement('option');
                    option.textContent = 'No users found';
                    option.disabled = true;
                    option.selected = true;
                    userSelect.appendChild(option);
                }
            })
            .catch(function (err) {
                console.error('Error fetching users:', err);
            });
    },

    _fetchPaymentAmountByCounter: function (counterId) {
        const self = this;
        rpc('/get/payment/amount/by/counter', { counter_id: counterId })
            .then(function (result) {
                if (result) {

                    self.$('#total_cash_field').val(parseFloat(result.total_cash || 0).toFixed(2));

                    self.$('#petty_cash_total_field').val(parseFloat(result.petty_cash_total || 0).toFixed(2));

                    self.$('#cash_in_hand').val(Math.trunc(parseFloat(result.cash_in_hand || 0)));
                }
            })
            .catch(function (err) {
                console.error('Error fetching payment amount:', err);
            });
    },



    _checkAlreadySubmitted: function () {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('already_submitted') === '1') {
            $('#already-submitted-modal').modal('show');
            const newUrl = window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
        }
    },
    _fetchPettyUsersByCounter: function (counterId) {
        const self = this;
        const loggedUserName = this.$('#person').val();

        rpc('/get/users/by/counter', { counter_id: counterId })
            .then(function (result) {
                const userSelect = self.$('#petty_to_user');
                userSelect.empty();
                if (result && result.users && result.users.length > 0) {
                    const filteredUsers = result.users.filter(user => user.name !== loggedUserName);

                    if (filteredUsers.length > 0) {
                        filteredUsers.forEach(user => {
                            userSelect.append(`<option value="${user.id}">${user.name}</option>`);
                        });
                    } else {
                        userSelect.append('<option disabled selected>No users found</option>');
                    }
                } else {
                    userSelect.append('<option disabled selected>No users found</option>');
                }
            })
            .catch(function (err) {
                console.error('Error fetching petty users:', err);
            });
    },
    _SubmitPettyCash: function (ev) {
        ev.preventDefault();
        const form = document.querySelector('#petty_cash_form');
        const formData = new FormData(form);

        formData.append('from_counter', $('#from_counter').val());
        formData.append('petty_to_user', $('#petty_to_user').val());
        formData.append('created_date', $('#created_date').val());

        fetch('/petty/cash/submit', {
            method: 'POST',
            body: formData
        })
            .then(response => {
                if (response.redirected) {
                    window.location.href = response.url;
                } else {
                    console.error('Petty cash submission failed.');
                }
            })
            .catch(err => {
                console.error('Error submitting petty cash:', err);
            });
    },
    _checkPettySuccess: function () {
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('petty_success') === '1') {
            $('#petty-success-modal').modal('show');
            const newUrl = window.location.pathname;
            window.history.replaceState({}, document.title, newUrl);
        }
    },

    _checkPettyCashByCounter: function (counterId) {
        const self = this;
        rpc('/check/petty/cash/by/counter', { counter_id: counterId })
            .then(function (result) {
                if (result.exists) {
                    $('#modal_from_user').text(result.from_user);
                    $('#modal_counter').text(result.counter);
                    $('#modal_date').text(result.date);
                    $('#modal_amount').text(result.amount.toFixed(2));

                    $('#pettyCashReviewModal').modal('show');

                    $('#accept_petty_cash').off('click').on('click', function () {
                        const currentTotal = parseFloat($('#total_cash_field').val()) || 0;
                        const newTotal = currentTotal + parseFloat(result.amount);
                        $('#total_cash_field').val(newTotal.toFixed(2));

                        rpc('/petty/cash/update/state', {
                            petty_id: result.id,
                            state: 'accepted'
                        });

                        $('#pettyCashReviewModal').modal('hide');
                    });

                    $('#reject_petty_cash').off('click').on('click', function () {
                        rpc('/petty/cash/update/state', {
                            petty_id: result.id,
                            state: 'rejected'
                        });
                        $('#pettyCashReviewModal').modal('hide');
                    });
                }
            })
            .catch(function (err) {
                console.error('Error checking petty cash:', err);
            });
    },


});

