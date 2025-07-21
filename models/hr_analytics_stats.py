from odoo import models, fields, api

class HRStats(models.Model):
    _name = "hr.analytics.stats"
    _description = "HR Analytics Statstics"
    
    name = fields.Char(
        string="Statistic Name",
        required=True,
        default="HR Stats")
    total_employees = fields.Integer(
        string="Total Employees",
        compute="_compute_stats")
    avg_turnover_rate = fields.Float(
        string="Average Turnover Rate",
        compute="_compute_stats")
    avg_salary_department = fields.Float(
        string="Average Salary by Department",
        compute="_compute_stats")
    total_leaves = fields.Integer(
        string="Total Leaves",
        compute="_compute_stats")
    avg_attendance_hours = fields.Float(
        string="Average Attendance Hours",
        compute="_compute_stats")
    department_id = fields.Many2one("hr.department", string="Department")
    
    def _compute_stats(self):
        for record in self:
            domain = [("active", "=", True)]
            if record.department_id:
                domain += [("department_id", "=", record.department_id.id)]
            # Total employees
            employees = self.env["hr.employee"].search(domain)
            record.total_employees = len(employees)
            # Average turnover rate
            record.avg_turnover_rate = sum(emp.turnover_rate for emp in employees) / len(employees) if employees else 0
            # Average salary
            record.avg_salary_department = sum(emp.avg_salary for emp in employees) / len(employees) if employees else 0
            # Total leaves (validated)
            leave_domain = [('state', '=', 'validate')]
            if record.department_id:
                leave_domain += [('employee_id.department_id', '=', record.department_id.id)]
            record.total_leaves = self.env['hr.leave'].search_count(leave_domain)
            # Average attendance hours
            att_domain = []
            if record.department_id:
                att_domain += [('employee_id.department_id', '=', record.department_id.id)]
            attendances = self.env['hr.attendance'].search(att_domain)
            worked_hours = attendances.mapped('worked_hours')
            record.avg_attendance_hours = sum(worked_hours) / len(worked_hours) if worked_hours else 0