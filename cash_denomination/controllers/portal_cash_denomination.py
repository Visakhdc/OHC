from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers import portal


class CustomerPortal(portal.CustomerPortal):
    """This class inherits controller portal"""
    def _prepare_home_portal_values(self, counters):
        """This function super the method and set count as none
        :param int counters: count of the cash denomination
        :param auth: The user must be authenticated and the current
        request will perform using the rights that the user was given.
        :param string type: HTTP Request and JSON Request,utilizing HTTP
        requests via the GET and POST methods. HTTP methods such as GET, POST,
        PUT, DELETE
        :return: values in counters
       """
        values = super()._prepare_home_portal_values(counters)
        if 'p_count' in counters:
            values['p_count'] = None
        return values

    @http.route('/cash/denomination/portal', type='http', auth="user", website=True)
    def portal_cash_denomination(self, **kw):
        return request.render("cash_denomination.portal_cash_denomination_template")


    @http.route('/cash/denomination/search', type='json', auth="user", website=True)
    def search_cash_denomination_rect(self, args):
        """To get corresponding records matching domain conditions
        :param args: Name input on search records
        :return: Result of input text given for searching the cash denomination record
        """
        cash_denomination_rec = request.env['cash.denomination']
        user = request.env.user
        search_term = args.get('product', False)
        domain = []

        if search_term:
            domain = ['|',
                    ('user.name', 'ilike', search_term),
                    ('counter', 'ilike', search_term)]

        res = cash_denomination_rec.with_user(user).search_read(
            domain=domain,
            fields=['id', 'user', 'counter', 'grand_total', 'date', 'state']
        )
        return res or False
