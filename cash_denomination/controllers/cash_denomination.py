from odoo import http
from odoo.http import request
from datetime import date
from datetime import datetime, time

class CashDenominationPageController(http.Controller):

    @http.route('/cash/denomination', type='http', auth='user', website=True)
    def cash_denomination_page(self, **kw):
        user = request.env.user
        today = date.today()
        start_datetime = datetime.combine(today, time.min)
        end_datetime = datetime.combine(today, time.max)
        cash_counter_model = request.env['cash.counter']
        account_payment_model = request.env['account.payment']
        cash_transfer_model = request.env['cash.transfer']
        counters = cash_counter_model.with_user(user).search([])


        logged_user_counter = cash_counter_model.with_user(user).search([('name', 'in', user.ids)], order='id asc')

        if not logged_user_counter:
            return request.redirect('/?no_counter_allocated=1')

        payment_receive = account_payment_model.with_user(user).search([('journal_id.type','=','cash'),
                                                                ('payment_type' ,'=', 'inbound'),
                                                                ('state', '=', 'paid'),
                                                                ('date', '=', today),
                                                                ])

        cash_transfer = cash_transfer_model.with_user(user).search([
            ('name', '=', user.id),
            ('date', '>=', start_datetime),
            ('date', '<=', end_datetime),
        ])
        cash_transfer_amt = sum(cash_transfer.mapped('amount'))
        total_received_amt = sum(payment_receive.mapped('amount'))
        cash_in_hand = total_received_amt - cash_transfer_amt

        outgoing_transfers = cash_transfer.with_user(user)

        incoming_transfers = cash_transfer.with_user(user).search([('transfer_to_user', '=', user.id)])

        return request.render("cash_denomination.website_cash_denomination", {
            'counters': logged_user_counter,
            'user': user,
            'total_cash': total_received_amt,
            'cash_in_hand': cash_in_hand,
            'to_counter': counters,
            'outgoing_transfers': outgoing_transfers,
            'incoming_transfers': incoming_transfers,
        })


    @http.route(['/cash/denomination/submit'], type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def cash_denomination_submit(self, **post):
        counter_id = post.get('counter')
        date_str = post.get('date')
        user = request.env.user
        cash_transfer_model = request.env['cash.transfer']
        cash_denomination_model = request.env['cash.denomination']

        line_values = [
            (0, 0, {
                'counts': int(value),
                'currency': key.split('_')[1],
            })
            for key, value in post.items()
            if key.startswith('counts_') and value and int(value) > 0
        ]

        transfer_records = cash_transfer_model.with_user(user).search([
            ('name', '=', user.id),
            ('from_counter', '=', int(counter_id)),
            ('create_date', '>=', f"{date_str} 00:00:00"),
            ('create_date', '<=', f"{date_str} 23:59:59"),
        ])

        transfer_lines = []
        for tr in transfer_records:
            transfer_lines.append((0, 0, {
                'from_counter': tr.from_counter.id,
                'to_counter': tr.to_counter.id,
                'amount': tr.amount,
                'remarks': tr.remarks,
                'transfer_date': tr.create_date,
                'to_user': tr.transfer_to_user.id if tr.transfer_to_user else False,
            }))

        cash_denomination_model.with_user(user).create({
            'date': date_str,
            'user': user.id,
            'counter': int(counter_id),
            'line_ids': line_values,
            'transfer_line_ids': transfer_lines,
        })

        return request.redirect('/cash/denomination?success=1')

    @http.route(['/cash/transfer/submit'], type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def transfer_cash_submit(self, **post):
        user = request.env.user

        from_counter_id = post.get('from_counter')
        to_counter_id = post.get('to_counter')
        transfer_amount = post.get('transfer_amount')
        remarks = post.get('remarks')
        transfer_to_user = post.get('transfer_to_user')
        cash_transfer_model = request.env['cash.transfer']

        cash_transfer_model.with_user(user).create({
            'name': request.env.user.id,
            'from_counter': int(from_counter_id) if from_counter_id else False,
            'transfer_to_user': transfer_to_user,
            'to_counter': int(to_counter_id) if to_counter_id else False,
            'amount': float(transfer_amount) if transfer_amount else 0.0,
            'remarks': remarks or '',
        })

        return request.redirect('/cash/denomination?transfer_success=1')

