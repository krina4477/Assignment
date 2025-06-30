from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('name', 'ref')
    def _compute_display_name(self):
        for partner in self:
            name = partner.name or ''
            if partner.ref:
                name += f' [{partner.ref}]'
            partner.display_name = name

    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = ['|', ('name', operator, name), ('ref', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

