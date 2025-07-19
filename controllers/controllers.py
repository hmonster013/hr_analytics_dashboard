# -*- coding: utf-8 -*-
# from odoo import http


# class HrAnalyticsDashboard(http.Controller):
#     @http.route('/hr_analytics_dashboard/hr_analytics_dashboard', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_analytics_dashboard/hr_analytics_dashboard/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_analytics_dashboard.listing', {
#             'root': '/hr_analytics_dashboard/hr_analytics_dashboard',
#             'objects': http.request.env['hr_analytics_dashboard.hr_analytics_dashboard'].search([]),
#         })

#     @http.route('/hr_analytics_dashboard/hr_analytics_dashboard/objects/<model("hr_analytics_dashboard.hr_analytics_dashboard"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_analytics_dashboard.object', {
#             'object': obj
#         })

