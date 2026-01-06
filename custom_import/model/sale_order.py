from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import io
import csv
import openpyxl
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_open_file_upload_wizard(self):
        """Open the file upload wizard"""
        return {
            'name': 'Upload File',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.file.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
            }
        }


class SaleOrderFileUploadWizard(models.TransientModel):
    _name = 'sale.order.file.upload.wizard'
    _description = 'Sale Order File Upload Wizard'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
    file_data = fields.Binary(string='Upload File', required=True, help='Upload your file here (CSV, XLSX)')
    file_name = fields.Char(string='File Name')
    file_type = fields.Selection([
        ('csv', 'CSV File'),
        ('xlsx', 'Excel File'),
    ], string='File Type', compute='_compute_file_type', store=True)

    @api.depends('file_name')
    def _compute_file_type(self):
        for record in self:
            if record.file_name:
                if record.file_name.endswith('.csv'):
                    record.file_type = 'csv'
                elif record.file_name.endswith(('.xlsx', '.xls')):
                    record.file_type = 'xlsx'
                else:
                    record.file_type = False
            else:
                record.file_type = False

    def action_upload_file(self):
        self.ensure_one()
        
        if not self.file_data:
            raise UserError('Please upload a file before proceeding.')
        
        if not self.file_type:
            raise UserError('Unsupported file format. Please upload CSV or Excel files only.')
        
        file_content = base64.b64decode(self.file_data)
        
        if self.file_type == 'csv':
            rows = self._read_csv_file(file_content)
        elif self.file_type == 'xlsx':
            rows = self._read_xlsx_file(file_content)
        
        result = self._import_sale_orders(rows)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Import completed! Created: ' + str(result["created"]) + ' orders',
                'type': 'success',
                'sticky': False,
            }
        }

    def _read_csv_file(self, file_content):
        try:
            csv_data = io.StringIO(file_content.decode('utf-8'))
            csv_reader = csv.DictReader(csv_data)
            return list(csv_reader)
        except Exception as e:
            raise UserError('Error reading CSV file: ' + str(e))

    def _read_xlsx_file(self, file_content):
        try:
            workbook = openpyxl.load_workbook(io.BytesIO(file_content))
            sheet = workbook.active  
            headers = []
            for cell in sheet[1]:
                headers.append(cell.value)
            
            rows = []
            for row in sheet.iter_rows(min_row=2, values_only=True):
                row_dict = {}
                for i in range(len(row)):
                    if i < len(headers) and headers[i]:
                        row_dict[headers[i]] = row[i]
                is_empty = True
                for value in row:
                    if value is not None and str(value).strip():
                        is_empty = False
                        break
                
                if not is_empty:
                    rows.append(row_dict)
            
            return rows
        except Exception as e:
            raise UserError('Error reading Excel file: ' + str(e))

    def _is_empty_value(self, value):
        if value is None:
            return True
        if isinstance(value, str):
            return value.strip() == ''
        return False

    def _import_sale_orders(self, rows):
        created_count = 0
        updated_count = 0
        orders_data = {}
        row_number = 1
        last_order_ref = None  
        last_customer = None
        last_company_id = None
        last_order_date = None
        
        for row in rows:
            row_number += 1
            order_ref = row.get('Order Reference')
            barcode_value = row.get('Order Lines/Product/Barcode')
            customer_value = row.get('Customer')
            
            if self._is_empty_value(barcode_value):
                raise UserError(f'Product Barcode is required at row {row_number}')
            
            if not self._is_empty_value(customer_value):
                customer_name = str(customer_value).strip()
                last_customer = customer_name
            elif last_customer:
                customer_name = last_customer
                row['Customer'] = last_customer
            else:
                raise UserError(f'Customer name is required at row {row_number}')
            
            if self._is_empty_value(order_ref):
                if last_order_ref:
                    order_ref = last_order_ref
                else:
                    order_ref = self.env['ir.sequence'].next_by_code('sale.order') or '/'
                    last_order_ref = order_ref
                row['Order Reference'] = order_ref 
            else:
                order_ref = str(order_ref).strip()
                last_order_ref = order_ref            

            company_value = row.get('Company', '')
            if company_value and not self._is_empty_value(company_value):
                company = self.env['res.company'].search([('name', '=', company_value)], limit=1)
                company_id = company.id if company else self.env.company.id
                last_company_id = company_id
            elif last_company_id:
                company_id = last_company_id
                row['Company'] = last_company_id
            else:
                company_id = self.env.company.id
                last_company_id = company_id
            
            order_date_str = row.get('Order Date', '')
            if order_date_str and not self._is_empty_value(order_date_str):
                try:
                    if isinstance(order_date_str, str):
                        order_date = datetime.strptime(order_date_str, '%Y-%m-%d %H:%M:%S').date()
                    else:
                        order_date = order_date_str.date() if hasattr(order_date_str, 'date') else order_date_str
                    last_order_date = order_date
                except:
                    order_date = last_order_date if last_order_date else fields.Date.today()
            elif last_order_date:
                order_date = last_order_date
                row['Order Date'] = last_order_date 
            else:
                order_date = fields.Date.today()
                last_order_date = order_date
            
            if self._is_empty_value(order_ref):
                if last_order_ref:
                    order_ref = last_order_ref
                else:
                    order_ref = self.env['ir.sequence'].next_by_code('sale.order') or '/'
                    last_order_ref = order_ref
                row['Order Reference'] = order_ref 
            else:
                order_ref = str(order_ref).strip()
                last_order_ref = order_ref
            
            if order_ref not in orders_data:
                orders_data[order_ref] = {
                    'header': row,
                    'lines': []
                }
            orders_data[order_ref]['lines'].append(row)
        
        for order_ref in orders_data:
            order_data = orders_data[order_ref]
            try:
                self._create_sale_order(order_ref, order_data)
                created_count += 1
            except Exception as e:
                _logger.error('Error processing order ' + order_ref + ': ' + str(e))
                raise UserError(f'Error processing order {order_ref}: {str(e)}')
        
        return {
            'created': created_count,
            'updated': updated_count,
        }
   

    def _create_sale_order(self, order_ref, order_data):
        header = order_data['header']
        
        company_value = header.get('Company')
        _logger.info('Company value: %s', company_value)
        if company_value and not self._is_empty_value(company_value):
            company = self.env['res.company'].search([('name', '=', company_value)], limit=1)
            company_id = company.id if company else self.env.company.id
        else:
            company_id = self.env.company.id
       
        customer_value = header.get('Customer')
        if self._is_empty_value(customer_value):
            raise UserError('Customer name is required for order ' + order_ref)
        
        customer_name = str(customer_value).strip()
        partner = self.env['res.partner'].search([('name', '=', customer_name)], limit=1)
        if not partner:
            raise UserError('No customer found with name "' + customer_name + '" for order ' + order_ref)
        
        order_date_str = header.get('Order Date', '')
        try:
            if isinstance(order_date_str, str) and order_date_str:
                order_date = datetime.strptime(order_date_str, '%Y-%m-%d %H:%M:%S')
            elif order_date_str:
                order_date = order_date_str
            else:
                order_date = fields.Datetime.now()
        except:
            order_date = fields.Datetime.now()
        
        order_vals = {
            'partner_id': partner.id,
            'date_order': order_date,
            'name': order_ref,
            'company_id': company_id,
        }

        sale_order = self.env['sale.order'].create(order_vals)

        for line_data in order_data['lines']:
            self._create_order_line(sale_order, line_data)
        
        return sale_order

    def _create_order_line(self, sale_order, line_data):
        barcode_value = line_data.get('Order Lines/Product/Barcode')
        
        if self._is_empty_value(barcode_value):
            raise UserError(f'Product barcode is required for order {sale_order.name}')
        
        barcode = str(barcode_value).strip()
        
        product = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)
        if not product:
            raise UserError('Product with barcode "' + barcode + '" not found in order ' + sale_order.name)
        
        quantity = line_data.get('Order Lines/Quantity', 1.0)
        if isinstance(quantity, str):
            quantity = float(quantity.replace(',', '.'))
        elif quantity is None:
            quantity = 1.0
        
        unit_price = line_data.get('Order Lines/Unit Price', 0.0)
        if isinstance(unit_price, str):
            unit_price = float(unit_price.replace(',', '.'))
        elif unit_price is None:
            unit_price = 0.0
        
        discount = line_data.get('Order Lines/Discount (%)', '0')
        if discount is None or discount == '':
            discount = 0.0
        elif isinstance(discount, str):
            discount = float(discount.replace('%', '').replace(',', '.').strip())
        
        uom_value = line_data.get('Order Lines/Unit of Measure')
        product_uom = product.uom_id  # Default to product's UOM
        
        if uom_value and not self._is_empty_value(uom_value):
            uom_name = str(uom_value).strip()
            uom = self.env['uom.uom'].search([('name', '=', uom_name)], limit=1)
            if uom:
                product_uom = uom
            else:
                _logger.warning(f'Unit of Measure "{uom_name}" not found for order {sale_order.name}, using product default')
        
        tax_ids = []
        tax_value = line_data.get('Order Lines/Taxes')
        
        if tax_value and not self._is_empty_value(tax_value):
            tax_names = str(tax_value).strip()
            tax_name_list = [t.strip() for t in tax_names.split(',')]
            
            for tax_name in tax_name_list:
                if tax_name:
                    tax = self.env['account.tax'].search([
                        ('name', '=', tax_name),
                        ('company_id', '=', sale_order.company_id.id),
                        ('type_tax_use', '=', 'sale')
                    ], limit=1)
                    
                    if tax:
                        tax_ids.append(tax.id)
                    else:
                        _logger.warning(f'Tax "{tax_name}" not found for company {sale_order.company_id.name} in order {sale_order.name}')
        
        if not tax_ids:
            tax_ids = product.taxes_id.ids
        
        line_vals = {
            'order_id': sale_order.id,
            'product_id': product.id,
            'product_uom_qty': quantity,
            'product_uom_id': product_uom.id,
            'price_unit': unit_price,
            'discount': discount,
            'tax_ids': [(6, 0, tax_ids)], 
        }
        
        return self.env['sale.order.line'].create(line_vals)