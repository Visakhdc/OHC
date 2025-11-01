from odoo.http import request

class UserUtility:

    @classmethod
    def get_or_create_user(cls, user_env, user_data):
        """Retrieve or create a user"""
        try:
            res_users_model = user_env['res.users']
            country_model = user_env['res.country']
            state_model = user_env['res.country.state']
            existing_user = res_users_model.search([('login', '=', user_data.login)], limit=1)

            if existing_user:
                return existing_user
            user_type = user_data.user_type.value
            partner_data = user_data.partner_data
            group_xml_id = 'base.group_portal' if user_type == 'portal' else 'base.group_user'

            user_vals = {
                'name': user_data.name,
                'login': user_data.login,
                'email': user_data.email,
                'groups_id': [(6, 0, [request.env.ref(group_xml_id).id])],
            }
            if user_data.password:
                user_vals['password'] = user_data.password

            res_user = res_users_model.create(user_vals)
            if not res_user:
                raise ValueError(f"User creation failed")

            res_partner = res_user.partner_id

            country = country_model.search([('code', '=', 'IN')], limit=1)
            state = state_model.search([
                ('name', 'ilike', partner_data.state),
                ('country_id', '=', country.id)
            ], limit=1)

            is_agent= True if partner_data.agent == True else False
            partner_vals = {
                'x_care_id': partner_data.x_care_id,
                'company_type': partner_data.partner_type.value,
                'email': partner_data.email,
                'phone': partner_data.phone,
                'vat': partner_data.pan,
                'country_id': country.id if country else False,
                'state_id': state.id if state else False,
                'agent': is_agent
            }

            res_partner.write(partner_vals)
            return res_user

        except Exception as e:
            return {str(e)}
