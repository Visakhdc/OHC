from odoo.http import request

class PartnerUtility:

    @classmethod
    def get_or_create_partner(cls,user_env, partner_data):
        """Retrieve or create partner"""
        try:
            res_partner_model = user_env['res.partner']
            country_model = user_env['res.country']
            state_model = user_env['res.country.state']
            res_partner = res_partner_model.search([('x_care_id', '=', partner_data.x_care_id)], limit=1)

            if not res_partner:
                country = country_model.search([('code', '=', 'IN')], limit=1)
                state = state_model.search([
                    ('name', 'ilike', partner_data.state),
                    ('country_id', '=', country.id)
                ], limit=1)

                res_partner = res_partner_model.create({
                    'name': partner_data.name,
                    'x_care_id': partner_data.x_care_id,
                    'company_type': partner_data.partner_type.value,
                    'email': partner_data.email,
                    'phone': partner_data.phone,
                    'country_id': country.id if country else False,
                    'state_id': state.id if state else False,
                })
            else:
                res_partner.name = partner_data.name

            return res_partner

        except Exception as e:
            return {'error': f"Error while creating/updating partner: {str(e)}"}