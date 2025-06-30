from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.constrains('name')
    def _check_unique_name(self):
        for rec in self:
            existing = self.search([('name', '=', rec.name), ('id', '!=', rec.id)], limit=1)
            if existing:
                raise ValidationError("Category name must be unique!")
