# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class PartnerLedgerCustomHandler(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'

    def _custom_options_initializer(self, report, options, previous_options):
        """
        Add opening_balance column to report options
        """
        super()._custom_options_initializer(report, options, previous_options=previous_options)

        has_opening_column = False
        for col in options.get('columns', []):
            if col.get('expression_label') == 'opening_balance':
                has_opening_column = True
                break

        if not has_opening_column:
            opening_column = {
                'name': _('Opening Balance'),
                'expression_label': 'opening_balance',
                'figure_type': 'monetary',
                'sortable': True,
                'column_group_key': 'default',
            }
            if len(options.get('columns', [])) > 1:
                options['columns'].insert(1, opening_column)
            else:
                options['columns'].append(opening_column)

        for col in options.get('columns', []):
            if col.get('expression_label') == 'balance':
                col['name'] = _('Closing Balance')
                break

    def _check_if_partner_has_initial_balance(self, partner_id, options):
        """
        Check if partner has Initial Balance line in report
        """
        try:
            init_balances = self._get_initial_balance_values([partner_id], options)

            if partner_id in init_balances:
                for col_key, values in init_balances[partner_id].items():
                    balance = values.get('balance', 0)
                    if balance != 0:
                        return True, balance
            return False, 0
        except Exception:
            return False, 0

    def _query_partners(self, report, options):
        """
        Get partner data - only add opening_balance if partner has initial balance
        """
        result = super()._query_partners(report, options)

        for partner, partner_values in result:
            partner_id = partner.id if partner else None

            has_initial_balance = False
            initial_balance_value = 0

            if partner_id:
                has_initial_balance, initial_balance_value = self._check_if_partner_has_initial_balance(partner_id,
                                                                                                        options)

            for col_key, values in partner_values.items():
                if has_initial_balance:
                    values['opening_balance'] = initial_balance_value
                else:
                    values['opening_balance'] = None

        return result

    def _get_report_line_partners(self, options, partner, partner_values, level_shift=0):
        """
        Show opening balance only if partner has initial balance
        """
        line_data = super()._get_report_line_partners(options, partner, partner_values, level_shift)

        partner_id = partner.id if partner else None

        has_initial_balance = False
        opening_balance_value = None

        if partner_id:
            has_initial_balance, opening_balance_value = self._check_if_partner_has_initial_balance(partner_id, options)

        if not has_initial_balance:
            opening_balance_value = None  # Empty

        if 'columns' in line_data:
            for i, col in enumerate(options.get('columns', [])):
                if col.get('expression_label') == 'opening_balance':
                    report = self.env['account.report'].browse(options['report_id'])

                    line_data['columns'][i] = report._build_column_dict(
                        opening_balance_value, col, options=options
                    )
                    break

        return line_data

    def _get_report_line_move_line(self, options, aml_query_result, partner_line_id, init_bal_by_col_group,
                                   level_shift=0):
        """
        Individual lines - opening balance is empty
        """
        aml_query_result['opening_balance'] = None

        return super()._get_report_line_move_line(
            options, aml_query_result, partner_line_id, init_bal_by_col_group, level_shift
        )

    def _get_report_line_total(self, options, totals_by_column_group):
        """
        Calculate total opening balance from partners with initial balance
        """
        # Get all partner IDs from the report
        report = self.env['account.report'].browse(options['report_id'])
        result = super()._query_partners(report, options)

        # Calculate total opening balance only from partners with initial balance
        total_opening = 0
        for partner, partner_values in result:
            partner_id = partner.id if partner else None

            if partner_id:
                has_initial_balance, initial_balance_value = self._check_if_partner_has_initial_balance(partner_id,
                                                                                                        options)
                if has_initial_balance:
                    total_opening += initial_balance_value

        # Add opening_balance to totals
        for col_key, values in totals_by_column_group.items():
            values['opening_balance'] = total_opening
        line_data = super()._get_report_line_total(options, totals_by_column_group)

        # Update opening balance column
        if 'columns' in line_data:
            for i, col in enumerate(options.get('columns', [])):
                if col.get('expression_label') == 'opening_balance':
                    report = self.env['account.report'].browse(options['report_id'])
                    line_data['columns'][i] = report._build_column_dict(
                        total_opening, col, options=options
                    )
                    break

        return line_data
class AccountMoveInherited(models.Model):
    _inherit = "account.move"

    move_type = fields.Selection(
        selection=[
            ('entry', 'Journal Entry'),
            ('out_invoice', 'Customer Invoice'),
            ('out_refund', 'Customer Credit Note'),
            ('in_invoice', 'Vendor Bill'),
            ('in_refund', 'Vendor Debit Note'),
            ('out_receipt', 'Sales Receipt'),
            ('in_receipt', 'Purchase Receipt'),
        ],
        string='Type',
        required=True,
        tracking=True,
        change_default=True,
        index=True,
        default="entry",
    )