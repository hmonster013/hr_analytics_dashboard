# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta


class HREmployee(models.Model):
    _inherit = "hr.employee"

    # Analytics fields
    department_turnover_rate = fields.Float(
        string="Department Turnover Rate (%)",
        compute="_compute_department_turnover_rate",
        help="Turnover rate for the employee's department"
    )
    current_salary = fields.Float(
        string="Current Salary",
        compute="_compute_current_salary",
        help="Current salary from active contract"
    )
    kpi_score = fields.Float(
        string="KPI Score",
        compute="_compute_kpi_score",
        help="Performance score based on attendance and leave patterns"
    )
    total_leaves_ytd = fields.Integer(
        string="Total Leaves (YTD)",
        compute="_compute_total_leaves_ytd",
        help="Total validated leaves this year"
    )
    avg_daily_hours = fields.Float(
        string="Average Daily Hours",
        compute="_compute_avg_daily_hours",
        help="Average working hours per day (last 30 days)"
    )

    @api.depends('department_id')
    def _compute_department_turnover_rate(self):
        """Calculate turnover rate for employee's department"""
        for record in self:
            if not record.department_id:
                record.department_turnover_rate = 0.0
                continue

            # Get all employees in department (active + inactive)
            total_dept_employees = self.env['hr.employee'].search_count([
                ('department_id', '=', record.department_id.id)
            ])

            # Get inactive employees in department
            inactive_dept_employees = self.env['hr.employee'].search_count([
                ('department_id', '=', record.department_id.id),
                ('active', '=', False)
            ])

            if total_dept_employees > 0:
                record.department_turnover_rate = (inactive_dept_employees / total_dept_employees) * 100
            else:
                record.department_turnover_rate = 0.0

    @api.depends('contract_ids', 'contract_ids.state', 'contract_ids.wage')
    def _compute_current_salary(self):
        """Get current salary from active contract"""
        for record in self:
            active_contract = record.contract_ids.filtered(
                lambda c: c.state == 'open'
            )
            if active_contract:
                # Get the most recent active contract
                record.current_salary = active_contract[0].wage
            else:
                record.current_salary = 0.0

    def _compute_kpi_score(self):
        """Calculate KPI score based on performance metrics"""
        for record in self:
            score = 100.0  # Start with perfect score

            # Factor 1: Leave usage (reduce score for excessive leaves)
            current_year = datetime.now().year
            leaves_count = self.env['hr.leave'].search_count([
                ('employee_id', '=', record.id),
                ('state', '=', 'validate'),
                ('request_date_from', '>=', f'{current_year}-01-01'),
                ('request_date_from', '<=', f'{current_year}-12-31')
            ])

            # Deduct 3 points per leave day (assuming reasonable leave allowance)
            score -= min(leaves_count * 3, 30)  # Max 30 points deduction

            # Factor 2: Attendance consistency (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', record.id),
                ('check_in', '>=', thirty_days_ago)
            ])

            # Check for attendance gaps (days without check-in)
            if attendances:
                attendance_days = len(set(att.check_in.date() for att in attendances))
                working_days = 22  # Approximate working days in 30 days
                attendance_rate = attendance_days / working_days if working_days > 0 else 0
                score *= attendance_rate  # Multiply by attendance rate

            record.kpi_score = max(0.0, min(100.0, score))

    def _compute_total_leaves_ytd(self):
        """Calculate total validated leaves for current year"""
        current_year = datetime.now().year
        for record in self:
            record.total_leaves_ytd = self.env['hr.leave'].search_count([
                ('employee_id', '=', record.id),
                ('state', '=', 'validate'),
                ('request_date_from', '>=', f'{current_year}-01-01'),
                ('request_date_from', '<=', f'{current_year}-12-31')
            ])

    def _compute_avg_daily_hours(self):
        """Calculate average daily working hours (last 30 days)"""
        thirty_days_ago = datetime.now() - timedelta(days=30)
        for record in self:
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', record.id),
                ('check_in', '>=', thirty_days_ago),
                ('worked_hours', '>', 0)
            ])

            if attendances:
                total_hours = sum(attendances.mapped('worked_hours'))
                working_days = len(set(att.check_in.date() for att in attendances))
                record.avg_daily_hours = total_hours / working_days if working_days > 0 else 0.0
            else:
                record.avg_daily_hours = 0.0