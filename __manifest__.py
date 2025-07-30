# -*- coding: utf-8 -*-
{
    'name': "HR Analytics Dashboard",
    'version': '1.0.0',
    'summary': "Advanced HR analytics dashboard with real-time metrics and visualizations",

    'description': """
HR Analytics Dashboard
======================

This module provides comprehensive HR analytics with:
* Real-time employee metrics and KPIs
* Interactive charts and visualizations
* Department-wise analytics
* Attendance and leave trends
* Salary distribution analysis
* Customizable date range filtering

Features:
---------
* Employee turnover rate tracking
* Average salary calculations by department
* KPI scoring based on performance metrics
* Attendance pattern analysis
* Leave usage trends
* Interactive dashboard with filters
    """,

    'author': "Your Company",
    'website': "https://www.yourcompany.com",
    'category': 'Human Resources',
    'license': 'LGPL-3',

    # Dependencies
    'depends': [
        'hr',
        'hr_attendance',
        'hr_holidays',
        'hr_contract',
        'web'
    ],

    # Data files
    'data': [
        'security/ir.model.access.csv',
        'views/hr_dashboard_views.xml',
    ],

    # Frontend assets
    'assets': {
        'web.assets_backend': [
            'hr_analytics_dashboard/static/src/js/chart_renderer.js',
            'hr_analytics_dashboard/static/src/js/dashboard.js',
            'hr_analytics_dashboard/static/src/xml/dashboard.xml',
        ],
    },

    'installable': True,
    'application': True,
    'auto_install': False,
}

