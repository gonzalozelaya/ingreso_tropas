from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _validate_session(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        """
        Valida la sesión sin generar asientos contables.
        """
        # Puedes registrar un log para confirmar que este método se ejecuta.
        _logger.info("Cerrando la sesión sin generar asientos contables.")
        
        # Omitir la creación de asientos contables
        self.write({'state': 'closed'})
        return True