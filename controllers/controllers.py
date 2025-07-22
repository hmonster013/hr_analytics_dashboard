import json

from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from collections import defaultdict

class HRAnalyticsController(http.Controller):
    @http.route("/hr_analytics/data", type="json", auth="user", methods=["POST"])
    def get_hr_data(self, department_id=None, start_date=None, end_date=None, **kwargs):
        """
        Get HR Analytics data with optional filters
        """
        print(f"Controller received: department_id={department_id}, start_date={start_date}, end_date={end_date}")
        
        # Convert department_id to int if provided
        if department_id and department_id != 'null' and department_id != '':
            try:
                department_id = int(department_id)
            except (ValueError, TypeError):
                department_id = None
        else:
            department_id = None
        
        # 1. Filter employees
        domain = [("active", "=", True)]
        if department_id:
            domain.append(('department_id', '=', department_id))
            print(f"Filtering by department: {department_id}")
        
        employees = request.env['hr.employee'].search(domain)
        print(f"Found {len(employees)} employees")

        # 2. Calculate real metrics
        total_employees = len(employees)
        
        # Calculate turnover rate (inactive employees vs total)
        all_employees_domain = []
        if department_id:
            all_employees_domain.append(('department_id', '=', department_id))
        
        total_all = request.env['hr.employee'].search_count(all_employees_domain)
        inactive_count = request.env['hr.employee'].search_count(all_employees_domain + [('active', '=', False)])
        turnover_rate = (inactive_count / total_all * 100) if total_all > 0 else 0
        
        # Calculate average salary from contracts
        contract_domain = [('state', '=', 'open')]
        if department_id:
            contract_domain.append(('employee_id.department_id', '=', str(department_id)))
        contracts = request.env['hr.contract'].search(contract_domain)
        wages = [contract.wage for contract in contracts if contract.wage]
        avg_salary = sum(wages) / len(wages) if wages else 0
        
        # Calculate KPI average (based on leave usage - fewer leaves = higher KPI)
        kpi_scores = []
        for emp in employees:
            leave_count = request.env['hr.leave'].search_count([
                ('employee_id', '=', emp.id),
                ('state', '=', 'validate')
            ])
            # KPI formula: 100 - (leave_days * 5), minimum 0
            kpi_score = max(0, 100 - (leave_count * 5))
            kpi_scores.append(kpi_score)
        
        kpi_average = sum(kpi_scores) / len(kpi_scores) if kpi_scores else 0

        data = {
            'total_employees': total_employees,
            'turnover_rate': round(turnover_rate, 2),
            'avg_salary': round(avg_salary, 2),
            'kpi_average': round(kpi_average, 2),
            'attendance_trends': [],
            'salary_distribution': [],
            'leave_trends': [],
            'avg_kpi': round(kpi_average, 2),
            'kpi_distribution': [],
        }

        print(f"Calculated metrics: turnover={turnover_rate:.2f}%, avg_salary={avg_salary:.2f}, kpi={kpi_average:.2f}")

        # 3. Date range processing
        if not start_date or not end_date:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
        else:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=30)

        print(f"Date range: {start_date} to {end_date}")

        # 4. Attendance trends
        date_domain = [
            ('check_in', '>=', start_date), 
            ('check_in', '<=', end_date)
        ]
        dept_domain = []
        if department_id:
            dept_domain = [('employee_id.department_id', '=', int(department_id))]
        att_domain = date_domain + dept_domain
        print(f"Attendance domain: {att_domain}")
        attendances = request.env['hr.attendance'].search(att_domain)
        print(f"Attendances found: {[{'id': a.id, 'emp': a.employee_id.name, 'hours': a.worked_hours} for a in attendances]}")
        att_by_day = defaultdict(list)
        for att in attendances:
            day = att.check_in.date().isoformat()
            att_by_day[day].append(att.worked_hours or 0)
        
        attendance_trends = [
            {"date": day, "worked_hours": sum(hours)/len(hours) if hours else 0}
            for day, hours in sorted(att_by_day.items())
        ]
        data['attendance_trends'] = attendance_trends

        # 5. Salary distribution by department
        all_contracts = request.env['hr.contract'].search([('state', '=', 'open')])
        salary_by_dept = defaultdict(float)
        for contract in all_contracts:
            if contract.employee_id and contract.employee_id.department_id:
                # If filtering by department, only include that department
                if department_id and contract.employee_id.department_id.id != department_id:
                    continue
                dept_name = contract.employee_id.department_id.name
                salary_by_dept[dept_name] += contract.wage or 0
        
        salary_distribution = [
            {"department": dept, "total_salary": total}
            for dept, total in salary_by_dept.items()
        ]
        data['salary_distribution'] = salary_distribution

        # 6. Leave trends by month
        leave_domain = [
            ('state', '=', 'validate'),
            ('request_date_from', '>=', start_date),
            ('request_date_from', '<=', end_date)
        ]
        if department_id:
            leave_domain.append(('employee_id.department_id', '=', department_id))
        
        leaves = request.env['hr.leave'].search(leave_domain)
        leave_by_month = defaultdict(int)
        for leave in leaves:
            if leave.request_date_from:
                month = leave.request_date_from.strftime('%Y-%m')
                leave_by_month[month] += 1
        
        leave_trends = [{"month": k, "count": v} for k, v in sorted(leave_by_month.items())]
        data['leave_trends'] = leave_trends

        # 7. KPI Distribution
        kpi_hist = defaultdict(int)
        for score in kpi_scores:
            bucket = int(score // 10) * 10
            kpi_hist[bucket] += 1
        
        kpi_distribution = [
            {"score_range": f"{bucket}-{bucket+9}", "count": count}
            for bucket, count in sorted(kpi_hist.items())
        ]
        data['kpi_distribution'] = kpi_distribution

        print(f"Returning data: total_employees={data['total_employees']}, attendance_trends={len(data['attendance_trends'])}")
        return data
