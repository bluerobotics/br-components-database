from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    bre_number = fields.Char(string='BRE Number', readonly=True)
    component_value = fields.Char(string='Value')
    datasheet = fields.Char(string='Datasheet')
    manufacturer = fields.Char(string='Manufacturer')
    mpn = fields.Char(string='Manufacturer Part Number')
    library = fields.Char(string='Library', readonly=True)
    component_sort = fields.Float(string='Component Sort', readonly=True)

    # Define the related field for the description in the BRE Data tab
    bre_description = fields.Char(string='Description', store=True)

    # Ensure synchronization between name and bre_description
    @api.onchange('bre_description')
    def _onchange_bre_description(self):
        if self.bre_description != self.name:
            self.name = self.bre_description

    @api.onchange('name')
    def _onchange_name(self):
        if self.name != self.bre_description:
            self.bre_description = self.name

    def generate_bre_number(self):
        """Generate the next BRE Number for the product and set it to the default_code field."""
        for record in self:
            if not record.bre_number:
                seq = self.env['ir.sequence'].next_by_code('product.bre.sequence')
                if not seq:
                    seq = 'BR-001000'  # Set a default start if sequence is not configured
                record.bre_number = seq
                record.default_code = seq

class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    jlcpcb_inventory = fields.Integer(string='JLCPCB Inventory', default=0)
    global_sourcing_inventory = fields.Integer(string='Global Sourcing Inventory', default=0)
    consigned_inventory = fields.Integer(string='Consigned Inventory', default=0)
