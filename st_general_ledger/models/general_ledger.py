# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from collections import defaultdict


class AccountGeneralLedgerReportHandlerInherit(models.AbstractModel):
    _inherit = 'account.general.ledger.report.handler'

    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals, warnings=None):
        super()._dynamic_lines_generator(report, options, all_column_groups_expression_totals, warnings)
        lines = []
        date_from = fields.Date.from_string(options['date']['date_from'])
        company_currency = self.env.company.currency_id

        totals_by_column_group = defaultdict(lambda: {'debit': 0, 'credit': 0, 'balance': 0})

        all_accounts_info = []
        for account, column_group_results in self._query_values(report, options):
            all_accounts_info.append((account, column_group_results))

        account_ids = [acc.id for acc, _ in all_accounts_info]
        init_balances_data = {}
        if account_ids:
            try:
                init_balances_data = self._get_initial_balance_values(report, account_ids, options)
            except Exception as e:
                init_balances_data = {}

        for account, column_group_results in all_accounts_info:
            eval_dict = {}
            has_lines = False

            init_balance_value = 0.0
            if account.id in init_balances_data:
                _, init_balance_dict = init_balances_data[account.id]
                for col_key in options['column_groups']:
                    if init_balance_dict.get(col_key):
                        init_balance_value = init_balance_dict[col_key].get('balance', 0.0)
                        break

            for column_group_key, results in column_group_results.items():
                account_sum = results.get('sum', {})
                account_un_earn = results.get('unaffected_earnings', {})

                account_debit = account_sum.get('debit', 0.0) + account_un_earn.get('debit', 0.0)
                account_credit = account_sum.get('credit', 0.0) + account_un_earn.get('credit', 0.0)
                account_balance = account_sum.get('balance', 0.0) + account_un_earn.get('balance', 0.0)

                eval_dict[column_group_key] = {
                    'amount_currency': account_sum.get('amount_currency', 0.0) + account_un_earn.get('amount_currency', 0.0),
                    'debit': account_debit,
                    'credit': account_credit,
                    'balance': account_balance,
                    'opening_balance': init_balance_value,
                }

                max_date = account_sum.get('max_date')
                has_lines = has_lines or (max_date and max_date >= date_from)

                totals_by_column_group[column_group_key]['debit'] += account_debit
                totals_by_column_group[column_group_key]['credit'] += account_credit
                totals_by_column_group[column_group_key]['balance'] += account_balance

            lines.append(self._get_account_title_line(report, options, account, has_lines, eval_dict))

        for totals in totals_by_column_group.values():
            totals['balance'] = company_currency.round(totals['balance'])

        journal_options = report._get_options_journals(options)
        if len(options['column_groups']) == 1 and len(journal_options) == 1 and journal_options[0]['type'] in ('sale',
                                                                                                               'purchase'):
            lines += self._tax_declaration_lines(report, options, journal_options[0]['type'])

        lines.append(self._get_total_line(report, options, totals_by_column_group))

        return [(0, line) for line in lines]