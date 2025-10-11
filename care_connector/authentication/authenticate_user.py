from odoo import http
from odoo.http import request
import base64


class UserAuthentication(http.Controller):

    @staticmethod
    def get_authenticated_user(auth_header):
        """Authenticate the user using Basic Auth credentials"""
        try:
            auth_decoded = base64.b64decode(auth_header.split(" ")[1]).decode("utf-8")
            username, password = auth_decoded.split(":", 1)
            credential = {'login': username, 'password': password, 'type': 'password'}
            session_data = request.session.authenticate(
                request.session.db, credential
            )
            if session_data and session_data.get("uid"):
                return session_data["uid"]
            return None

        except Exception as e:
            return None