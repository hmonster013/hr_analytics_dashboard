from odoo import models, fields, api

class HREmployee(models.Model):
    _inherit = "hr.employee"
    
    turnover_rate = fields.Float()
    avg_salary = fields.Float()
    kpi_score = fields.Float()
    
    @api.depends("active", "department_id")
    def _compute_turnover_rate(self):
        total_employees = self.env["hr.employee"].search_count([("active", "=", True)])
        inactive = self.env["hr.employee"].search_count([("active", "=", False)])
        rate = (inactive / total_employees) * 100 if total_employees else 0
        for record in self:
            record.turnover_rate = rate
    
    @api.depends("contract_id.wage")    
    def _compute_avg_salary(self):
        for record in self:
            contracts = self.env["hr.contract"].search([("employee_id", "=", record.id)])
            wages = contracts.mapped("wage")
            record.avg_salary = sum(wages) / len(wages) if wages else 0
    
    def _compute_kpi_score(self):
        for record in self:
            leaves = self.env["hr.leave"].search_count([
                ("employee_id", "=", record.id),
                ("state", "=", "validate")])
            record.kpi_score = max(0, 100 - (leaves * 5))