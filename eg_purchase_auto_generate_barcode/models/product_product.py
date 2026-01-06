import base64

from odoo import models, api, fields
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    barcode_image = fields.Binary(string='Barcode Image')

    def generate_barcode(self):
        """
        automatically generate a barcode
        'Codabar', 'Code11', 'Code128', 'EAN13', 'EAN8', 'Extended39',
        'Extended93', 'FIM', 'I2of5', 'MSI', 'POSTNET', 'QR', 'Standard39', 'Standard93',
        'UPCA', 'USPS_4State'
        :return:
        """
        if not self.barcode:
            self.barcode = self.env['ir.sequence'].next_by_code('product.barcode.sequence')
        else:
            raise ValidationError("Already Generated Barcode you can Change Manually!!!")

    def generate_barcode_image(self):
        """
        Generate a Barcode Image
        :return:
        """
        self.barcode_image = base64.b64encode(
            self.env['ir.actions.report'].barcode('Code128', self.barcode, width=600,
                                                  height=150, humanreadable=1))

    def barcode_change(self):
        """This Method call when generate sequence but already barcode generate when raise a warning message"""
        if self.barcode:
            raise ValidationError("Change your Barcode sequence")
        else:
            self.generate_barcode()

    @api.model_create_multi
    def create(self, vals_list):
        """When create a record then automatically generate a barcode"""
        res = super(ProductProduct, self).create(vals_list)

        for rec in res:
            if not rec.barcode:
                rec.generate_barcode()
        return res
