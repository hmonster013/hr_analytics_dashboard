# -*- coding: utf-8 -*-
{
    'name': "HR Analytics Dashboard",
    'version': '1.0',
    'summary': "Custom dashboard for HR analytics in Odoo 18",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr', 'hr_attendance', 'hr_holidays', 'hr_contract'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/hr_dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_analytics_dashboard/static/src/js/dashboard.js',
            'hr_analytics_dashboard/static/src/xml/dashboard.xml',
            'hr_analytics_dashboard/static/src/js/chart_renderer.js',
        ],
    },
    'application': True,
}

