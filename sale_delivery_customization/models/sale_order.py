from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _action_confirm(self):
        res = super()._action_confirm()
        for order in self:
            pickings = order.picking_ids.filtered(lambda p: p.state not in ['done', 'cancel'])
            for picking in pickings:
                picking.tag_ids = [(6, 0, order.tag_ids.ids)]

        return res
