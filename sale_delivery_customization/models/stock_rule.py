from odoo import models
from collections import defaultdict
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.tools.float_utils import float_compare
from odoo.exceptions import UserError
from collections import defaultdict
from itertools import groupby
from dateutil.relativedelta import relativedelta
from odoo.addons.stock.models.stock_rule import ProcurementException

class StockRule(models.Model):
    _inherit = 'stock.rule'

    @api.model
    def _run_buy(self, procurements):
        procurements_by_group = defaultdict(list)
        errors = []

        for procurement, rule in procurements:
            date_planned = fields.Datetime.from_string(procurement.values['date_planned'])
            company_id = rule.company_id or procurement.company_id

            supplier = False
            if procurement.values.get('supplierinfo_id'):
                supplier = procurement.values['supplierinfo_id']
            elif procurement.values.get('orderpoint_id') and procurement.values['orderpoint_id'].supplier_id:
                supplier = procurement.values['orderpoint_id'].supplier_id
            else:
                supplier = procurement.product_id.with_company(company_id.id)._select_seller(
                    partner_id=self._get_partner_id(procurement.values, rule),
                    quantity=procurement.product_qty,
                    date=max(date_planned.date(), fields.Date.today()),
                    uom_id=procurement.product_uom,
                )

            supplier = supplier or procurement.product_id._prepare_sellers(False).filtered(
                lambda s: not s.company_id or s.company_id == company_id
            )[:1]

            if not supplier:
                errors.append((procurement, _('No vendor found for product %s.') % procurement.product_id.display_name))
                continue

            partner = supplier.partner_id
            procurement.values['supplier'] = supplier
            procurement.values['propagate_cancel'] = rule.propagate_cancel

            category_id = procurement.product_id.categ_id.id

            origin_group = procurement.origin
            if origin_group and origin_group.startswith('OP/'):
                continue
            origin_group = origin_group or 'no_origin'

            group_key = (rule, partner, category_id, origin_group)
            procurements_by_group[group_key].append((procurement, rule))

        if errors:
            raise ProcurementException(errors)

        for (rule, partner, category_id, origin_group), group_procs in procurements_by_group.items():
            procurements, rules = zip(*group_procs)
            company_id = rule.company_id or procurements[0].company_id
            supplier = procurements[0].values['supplier']
            partner = supplier.partner_id

            positive_values = [p.values for p in procurements if float_compare(
                p.product_qty, 0.0, precision_rounding=p.product_uom.rounding) >= 0]
            if not positive_values:
                continue

            origins = set(
                p.origin for p in procurements
                if p.origin and not p.origin.startswith('OP/')
            )

            po_vals = rule._prepare_purchase_order(company_id, origins, positive_values)

            #Create new PO
            po = self.env['purchase.order'].with_company(company_id).with_user(
                self.env.ref('base.user_admin').id).create(po_vals)

            #Prepare PO lines
            procurements_to_merge = self._get_procurements_to_merge(procurements)
            procurements = self._merge_procurements(procurements_to_merge)

            po_lines_by_product = {}
            grouped_po_lines = groupby(
                po.order_line.filtered(lambda l: not l.display_type and l.product_uom == l.product_id.uom_po_id),
                key=lambda l: l.product_id.id
            )
            for product, po_lines in grouped_po_lines:
                po_lines_by_product[product] = self.env['purchase.order.line'].concat(*po_lines)

            po_line_vals = []
            for procurement in procurements:
                existing_lines = po_lines_by_product.get(procurement.product_id.id, self.env['purchase.order.line'])
                po_line = existing_lines._find_candidate(*procurement)

                if po_line:
                    vals = self._update_purchase_order_line(
                        procurement.product_id,
                        procurement.product_qty,
                        procurement.product_uom,
                        company_id,
                        procurement.values,
                        po_line,
                    )
                    po_line.sudo().write(vals)
                else:
                    if float_compare(procurement.product_qty, 0.0,
                                     precision_rounding=procurement.product_uom.rounding) <= 0:
                        continue
                    po_line_vals.append(self.env['purchase.order.line']._prepare_purchase_order_line_from_procurement(
                        *procurement, po))

                    order_date_planned = procurement.values['date_planned'] - relativedelta(
                        days=procurement.values['supplier'].delay)
                    if fields.Date.to_date(order_date_planned) < fields.Date.to_date(po.date_order):
                        po.date_order = order_date_planned

            self.env['purchase.order.line'].sudo().create(po_line_vals)
