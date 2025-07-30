# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta


class HRAnalyticsStats(models.Model):
    _name = "hr.analytics.stats"
    _description = "HR Analytics Statistics"
    _order = "create_date desc"

    # Basic info
    name = fields.Char(
        string="Report Name",
        required=True,
        default=lambda self: f"HR Analytics - {datetime.now().strftime('%Y-%m-%d')}"
    )
    department_id = fields.Many2one(
        "hr.department",
        string="Department",
        help="Leave empty for company-wide statistics"
    )
    date_from = fields.Date(
        string="Date From",
        default=lambda self: datetime.now().date() - timedelta(days=30),
        help="Start date for analytics calculation"
    )
    date_to = fields.Date(
        string="Date To",
        default=lambda self: datetime.now().date(),
        help="End date for analytics calculation"
    )

    # Employee metrics
    total_employees = fields.Integer(
        string="Total Active Employees",
        compute="_compute_employee_stats",
        store=True
    )
    total_inactive_employees = fields.Integer(
        string="Total Inactive Employees",
        compute="_compute_employee_stats",
        store=True
    )
    turnover_rate = fields.Float(
        string="Turnover Rate (%)",
        compute="_compute_employee_stats",
        store=True,
        help="Percentage of inactive employees"
    )

    # Salary metrics
    avg_salary = fields.Float(
        string="Average Salary",
        compute="_compute_salary_stats",
        store=True
    )
    total_salary_cost = fields.Float(
        string="Total Salary Cost",
        compute="_compute_salary_stats",
        store=True
    )

    # Leave metrics
    total_leaves = fields.Integer(
        string="Total Leaves (Period)",
        compute="_compute_leave_stats",
        store=True
    )
    avg_leaves_per_employee = fields.Float(
        string="Average Leaves per Employee",
        compute="_compute_leave_stats",
        store=True
    )

    # Attendance metrics
    avg_daily_hours = fields.Float(
        string="Average Daily Hours",
        compute="_compute_attendance_stats",
        store=True
    )
    total_worked_hours = fields.Float(
        string="Total Worked Hours (Period)",
        compute="_compute_attendance_stats",
        store=True
    )

    # KPI metrics
    avg_kpi_score = fields.Float(
        string="Average KPI Score",
        compute="_compute_kpi_stats",
        store=True
    )

    @api.depends('department_id')
    def _compute_employee_stats(self):
        """Compute employee-related statistics"""
        for record in self:
            domain = []
            if record.department_id:
                domain.append(('department_id', '=', record.department_id.id))

            # Active employees
            active_employees = self.env['hr.employee'].search_count(
                domain + [('active', '=', True)]
            )

            # Inactive employees
            inactive_employees = self.env['hr.employee'].search_count(
                domain + [('active', '=', False)]
            )

            total = active_employees + inactive_employees

            record.total_employees = active_employees
            record.total_inactive_employees = inactive_employees
            record.turnover_rate = (inactive_employees / total * 100) if total > 0 else 0.0

    @api.depends('department_id', 'total_employees')
    def _compute_salary_stats(self):
        """Compute salary-related statistics"""
        for record in self:
            contract_domain = [('state', '=', 'open')]
            if record.department_id:
                contract_domain.append(('employee_id.department_id', '=', record.department_id.id))

            contracts = self.env['hr.contract'].search(contract_domain)
            wages = contracts.mapped('wage')

            if wages:
                record.avg_salary = sum(wages) / len(wages)
                record.total_salary_cost = sum(wages)
            else:
                record.avg_salary = 0.0
                record.total_salary_cost = 0.0

    @api.depends('department_id', 'date_from', 'date_to', 'total_employees')
    def _compute_leave_stats(self):
        """Compute leave-related statistics"""
        for record in self:
            leave_domain = [
                ('state', '=', 'validate'),
                ('request_date_from', '>=', record.date_from),
                ('request_date_from', '<=', record.date_to)
            ]
            if record.department_id:
                leave_domain.append(('employee_id.department_id', '=', record.department_id.id))

            total_leaves = self.env['hr.leave'].search_count(leave_domain)

            record.total_leaves = total_leaves
            record.avg_leaves_per_employee = (
                total_leaves / record.total_employees
                if record.total_employees > 0 else 0.0
            )

    @api.depends('department_id', 'date_from', 'date_to')
    def _compute_attendance_stats(self):
        """Compute attendance-related statistics"""
        for record in self:
            att_domain = [
                ('check_in', '>=', record.date_from),
                ('check_in', '<=', record.date_to),
                ('worked_hours', '>', 0)
            ]
            if record.department_id:
                att_domain.append(('employee_id.department_id', '=', record.department_id.id))

            attendances = self.env['hr.attendance'].search(att_domain)
            worked_hours = attendances.mapped('worked_hours')

            if worked_hours:
                record.total_worked_hours = sum(worked_hours)
                # Calculate average daily hours
                days_in_period = (record.date_to - record.date_from).days + 1
                unique_days = len(set(att.check_in.date() for att in attendances))
                record.avg_daily_hours = (
                    sum(worked_hours) / unique_days
                    if unique_days > 0 else 0.0
                )
            else:
                record.total_worked_hours = 0.0
                record.avg_daily_hours = 0.0

    @api.depends('department_id', 'total_employees')
    def _compute_kpi_stats(self):
        """Compute KPI-related statistics"""
        for record in self:
            employee_domain = [('active', '=', True)]
            if record.department_id:
                employee_domain.append(('department_id', '=', record.department_id.id))

            employees = self.env['hr.employee'].search(employee_domain)

            if employees:
                # Force computation of KPI scores
                employees._compute_kpi_score()
                kpi_scores = employees.mapped('kpi_score')
                record.avg_kpi_score = sum(kpi_scores) / len(kpi_scores) if kpi_scores else 0.0
            else:
                record.avg_kpi_score = 0.0

    def action_refresh_stats(self):
        """Manual refresh of all statistics"""
        self._compute_employee_stats()
        self._compute_salary_stats()
        self._compute_leave_stats()
        self._compute_attendance_stats()
        self._compute_kpi_stats()
        return True