# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from collections import defaultdict

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HRAnalyticsController(http.Controller):

    # Constants
    DEFAULT_DAYS_RANGE = 30
    KPI_LEAVE_PENALTY = 3  # Points deducted per leave day
    MAX_KPI_LEAVE_PENALTY = 30  # Maximum points deducted for leaves

    @http.route("/hr_analytics/data", type="json", auth="user", methods=["POST"])
    def get_hr_data(self, department_id=None, start_date=None, end_date=None, **_kwargs):
        """
        Get HR Analytics data with optional filters

        Args:
            department_id (int, optional): Filter by department ID
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format

        Returns:
            dict: HR analytics data including metrics and trends
        """
        try:
            # Validate and process parameters
            department_id = self._validate_department_id(department_id)
            start_date, end_date = self._validate_date_range(start_date, end_date)

            _logger.info(f"HR Analytics request: dept={department_id}, dates={start_date} to {end_date}")

            # Get base employee data
            employees = self._get_filtered_employees(department_id)

            # Calculate core metrics
            metrics = self._calculate_core_metrics(employees, department_id)

            # Calculate trend data
            trends = self._calculate_trends(department_id, start_date, end_date)

            # Combine all data
            data = {**metrics, **trends}

            _logger.info(f"HR Analytics response: {len(employees)} employees, {len(data)} data points")
            return data

        except Exception as e:
            _logger.error(f"Error in HR Analytics controller: {str(e)}")
            return self._error_response(str(e))

    def _validate_department_id(self, department_id):
        """Validate and convert department_id parameter"""
        if not department_id or department_id in ('null', '', 'false'):
            return None

        try:
            dept_id = int(department_id)
            # Verify department exists
            if not request.env['hr.department'].browse(dept_id).exists():
                raise ValidationError(f"Department {dept_id} does not exist")
            return dept_id
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid department_id: {department_id}")

    def _validate_date_range(self, start_date, end_date):
        """Validate and convert date range parameters"""
        try:
            if not start_date or not end_date:
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=self.DEFAULT_DAYS_RANGE)
            else:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            # Validate date range
            if start_date > end_date:
                raise ValidationError("Start date cannot be after end date")

            # Limit range to prevent performance issues
            if (end_date - start_date).days > 365:
                raise ValidationError("Date range cannot exceed 365 days")

            return start_date, end_date

        except ValueError as e:
            raise ValidationError(f"Invalid date format. Use YYYY-MM-DD: {str(e)}")

    def _get_filtered_employees(self, department_id):
        """Get employees filtered by department"""
        domain = [("active", "=", True)]
        if department_id:
            domain.append(('department_id', '=', department_id))

        return request.env['hr.employee'].search(domain)

    def _calculate_core_metrics(self, employees, department_id):
        """Calculate core HR metrics"""
        total_employees = len(employees)

        # Turnover rate
        turnover_rate = self._calculate_turnover_rate(department_id)

        # Average salary
        avg_salary = self._calculate_average_salary(department_id)

        # KPI average
        kpi_average, kpi_distribution = self._calculate_kpi_metrics(employees)

        return {
            'total_employees': total_employees,
            'turnover_rate': round(turnover_rate, 2),
            'avg_salary': round(avg_salary, 2),
            'kpi_average': round(kpi_average, 2),
            'avg_kpi': round(kpi_average, 2),  # Backward compatibility
            'kpi_distribution': kpi_distribution,
        }

    def _calculate_turnover_rate(self, department_id):
        """Calculate turnover rate for department or company"""
        domain = []
        if department_id:
            domain.append(('department_id', '=', department_id))

        total_all = request.env['hr.employee'].search_count(domain)
        inactive_count = request.env['hr.employee'].search_count(
            domain + [('active', '=', False)]
        )

        return (inactive_count / total_all * 100) if total_all > 0 else 0.0

    def _calculate_average_salary(self, department_id):
        """Calculate average salary from active contracts"""
        contract_domain = [('state', '=', 'open')]
        if department_id:
            contract_domain.append(('employee_id.department_id', '=', department_id))

        contracts = request.env['hr.contract'].search(contract_domain)
        wages = [contract.wage for contract in contracts if contract.wage]

        return sum(wages) / len(wages) if wages else 0.0

    def _calculate_kpi_metrics(self, employees):
        """Calculate KPI metrics for employees"""
        kpi_scores = []

        for emp in employees:
            # Force computation of KPI score
            emp._compute_kpi_score()
            kpi_scores.append(emp.kpi_score)

        kpi_average = sum(kpi_scores) / len(kpi_scores) if kpi_scores else 0.0

        # KPI distribution
        kpi_hist = defaultdict(int)
        for score in kpi_scores:
            bucket = int(score // 10) * 10
            kpi_hist[bucket] += 1

        kpi_distribution = [
            {"score_range": f"{bucket}-{bucket+9}", "count": count}
            for bucket, count in sorted(kpi_hist.items())
        ]

        return kpi_average, kpi_distribution

    def _calculate_trends(self, department_id, start_date, end_date):
        """Calculate trend data for charts"""
        return {
            'attendance_trends': self._get_attendance_trends(department_id, start_date, end_date),
            'salary_distribution': self._get_salary_distribution(department_id),
            'leave_trends': self._get_leave_trends(department_id, start_date, end_date),
        }

    def _get_attendance_trends(self, department_id, start_date, end_date):
        """Get attendance trends by day"""
        att_domain = [
            ('check_in', '>=', start_date),
            ('check_in', '<=', end_date),
            ('worked_hours', '>', 0)
        ]
        if department_id:
            att_domain.append(('employee_id.department_id', '=', department_id))

        attendances = request.env['hr.attendance'].search(att_domain)

        # Group by day
        att_by_day = defaultdict(list)
        for att in attendances:
            day = att.check_in.date().isoformat()
            att_by_day[day].append(att.worked_hours)

        # Calculate average hours per day
        attendance_trends = [
            {
                "date": day,
                "worked_hours": round(sum(hours) / len(hours), 2) if hours else 0
            }
            for day, hours in sorted(att_by_day.items())
        ]

        return attendance_trends

    def _get_salary_distribution(self, department_id):
        """Get salary distribution by department"""
        contract_domain = [('state', '=', 'open')]

        # If filtering by specific department, only show that department
        if department_id:
            contract_domain.append(('employee_id.department_id', '=', department_id))

        contracts = request.env['hr.contract'].search(contract_domain)

        salary_by_dept = defaultdict(float)
        for contract in contracts:
            if contract.employee_id and contract.employee_id.department_id:
                dept_name = contract.employee_id.department_id.name
                salary_by_dept[dept_name] += contract.wage or 0

        salary_distribution = [
            {"department": dept, "total_salary": round(total, 2)}
            for dept, total in salary_by_dept.items()
        ]

        return salary_distribution

    def _get_leave_trends(self, department_id, start_date, end_date):
        """Get leave trends by month"""
        leave_domain = [
            ('state', '=', 'validate'),
            ('request_date_from', '>=', start_date),
            ('request_date_from', '<=', end_date)
        ]
        if department_id:
            leave_domain.append(('employee_id.department_id', '=', department_id))

        leaves = request.env['hr.leave'].search(leave_domain)

        # Group by month
        leave_by_month = defaultdict(int)
        for leave in leaves:
            if leave.request_date_from:
                month = leave.request_date_from.strftime('%Y-%m')
                leave_by_month[month] += 1

        leave_trends = [
            {"month": month, "count": count}
            for month, count in sorted(leave_by_month.items())
        ]

        return leave_trends

    def _error_response(self, error_message):
        """Return standardized error response"""
        return {
            'error': True,
            'message': error_message,
            'total_employees': 0,
            'turnover_rate': 0,
            'avg_salary': 0,
            'kpi_average': 0,
            'avg_kpi': 0,
            'attendance_trends': [],
            'salary_distribution': [],
            'leave_trends': [],
            'kpi_distribution': [],
        }

    @http.route("/hr_analytics/departments", type="json", auth="user", methods=["GET"])
    def get_departments(self):
        """Get list of departments for filter dropdown"""
        try:
            departments = request.env['hr.department'].search([])
            return [
                {'id': dept.id, 'name': dept.name}
                for dept in departments
            ]
        except Exception as e:
            _logger.error(f"Error getting departments: {str(e)}")
            return []
