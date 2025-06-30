# models/mrp_production.py

from odoo import models, fields, api
from odoo.exceptions import UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    sale_order_id = fields.Many2one('sale.order', string="Sale Order", compute='_compute_sale_order_id', store=True)

    @api.depends('origin')
    def _compute_sale_order_id(self):
        for mo in self:
            if mo.origin:
                sale = self.env['sale.order'].search([('name', '=', mo.origin)], limit=1)
                mo.sale_order_id = sale
            else:
                mo.sale_order_id = False

    def write(self, vals):
        for mo in self:
            old_qty = mo.product_qty
            res = super(MrpProduction, self).write(vals)

            new_qty = mo.product_qty
            if old_qty != new_qty and mo.state != 'draft' and mo.sale_order_id:
                raise UserError("You cannot change the quantity after confirmation for MOs created from Sale Orders.")

        return res
