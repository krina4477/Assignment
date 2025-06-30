from odoo import models, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    tag_ids = fields.Many2many('crm.tag', string="Tags")

    def button_validate(self):
        res = super().button_validate()
        for picking in self:
            if picking.picking_type_code == 'outgoing' and picking.state == 'done' and picking.sale_id and picking.sale_id.user_id:
                template = self.env.ref('sale_delivery_customization.mail_template_delivery_done_notify_salesperson',
                                        raise_if_not_found=False)
                if template:
                    template.send_mail(picking.id, force_send=True)
        return res
