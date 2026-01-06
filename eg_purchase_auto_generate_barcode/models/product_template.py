import base64

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

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
        if self.barcode:
            self.barcode_image = base64.b64encode(
                self.env['ir.actions.report'].barcode('Code128', self.barcode, width=600,
                                                      height=150, humanreadable=1))
        else:
            raise ValidationError('Please Generate Barcode Number!!!')

    def barcode_change(self):
        """This Method call when generate sequence but already barcode generate when raise a warning message"""
        if self.barcode:
            raise ValidationError("Change your Barcode sequence")
        else:
            self.generate_barcode()

    @api.model
    def create(self, vals_list):
        """When create a record then automatically generate a barcode"""
        res = super(ProductTemplate, self).create(vals_list)
        if not res.barcode:
            res.generate_barcode()
            # res.generate_barcode_image()
        return res
