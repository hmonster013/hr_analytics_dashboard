# HR Analytics Dashboard

A comprehensive HR analytics dashboard for Odoo 18 that provides real-time insights into employee metrics, attendance patterns, and performance indicators.

## Features

- **Real-time Metrics**: Live employee count, turnover rates, and salary analytics
- **Interactive Charts**: Visual representation of attendance trends, KPI distribution, and salary breakdown
- **Department Filtering**: Filter all metrics by specific departments
- **Date Range Selection**: Analyze data for custom time periods
- **Auto-refresh**: Automatic data updates every 30 seconds
- **PDF Export**: Export dashboard reports to PDF format
- **Responsive Design**: Works on desktop and mobile devices
- **Performance Optimized**: Efficient queries and caching for large datasets
- **Error Handling**: Robust error handling and user feedback

## Installation

1. Copy this module to your Odoo addons directory
2. Update the apps list in Odoo
3. Install the "HR Analytics Dashboard" module
4. Navigate to HR > Analytics Dashboard

## Dependencies

- hr (Human Resources)
- hr_attendance (Attendance Management)
- hr_holidays (Time Off Management)
- hr_contract (Contracts)
- web (Web Framework)

## Usage

### Dashboard Access
Navigate to **HR > Analytics Dashboard** to view the main dashboard.

### Key Metrics
- **Total Employees**: Current active employee count with drill-down capability
- **Turnover Rate**: Department-specific turnover percentage
- **Average Salary**: Mean salary from active contracts
- **KPI Score**: Performance score based on attendance and leave patterns

### Charts and Analytics
- **Attendance Trends**: Daily average working hours with trend analysis
- **KPI Distribution**: Employee performance score distribution by ranges
- **Salary Distribution**: Total salary costs by department (pie chart)

### Advanced Features
- **Real-time Updates**: Auto-refresh every 30 seconds (configurable)
- **Department Filtering**: Filter all metrics by specific department
- **Date Range Selection**: Custom date ranges up to 365 days
- **PDF Export**: Generate comprehensive reports with all charts
- **Responsive Design**: Mobile-friendly interface

## Technical Details

### Models
- `hr.analytics.stats`: Core analytics model with computed statistics
- Extended `hr.employee`: Additional computed fields for analytics
  - `department_turnover_rate`: Department-specific turnover rate
  - `current_salary`: Current salary from active contract
  - `kpi_score`: Performance score (0-100)
  - `total_leaves_ytd`: Year-to-date leave count
  - `avg_daily_hours`: Average daily working hours

### Controllers
- `/hr_analytics/data`: Main API endpoint for dashboard data
- `/hr_analytics/departments`: Department list for filters

### Security
- **Base Users**: Read access to analytics
- **HR Users**: Read/write access to analytics
- **HR Managers**: Full access including create/update/delete

### Performance Features
- Computed fields with proper dependencies
- Efficient database queries with domain filtering
- Date range validation (max 365 days)
- Error handling and logging
- Optimized chart rendering

## Configuration

The module works out of the box with default Odoo HR modules. No additional configuration required.

### Optional Configuration
- Auto-refresh interval can be modified in JavaScript
- Chart colors and styling can be customized in templates
- KPI calculation formula can be adjusted in models

## API Documentation

### GET /hr_analytics/data
Returns comprehensive HR analytics data.

**Parameters:**
- `department_id` (optional): Filter by department ID
- `start_date` (optional): Start date in YYYY-MM-DD format
- `end_date` (optional): End date in YYYY-MM-DD format

**Response:**
```json
{
  "total_employees": 150,
  "turnover_rate": 5.2,
  "avg_salary": 75000.00,
  "kpi_average": 87.5,
  "attendance_trends": [...],
  "salary_distribution": [...],
  "leave_trends": [...],
  "kpi_distribution": [...]
}
```

## Troubleshooting

### Common Issues
1. **Charts not displaying**: Ensure Chart.js library is properly loaded
2. **Data not updating**: Check user permissions and module dependencies
3. **PDF export failing**: Verify browser supports required libraries
4. **Performance issues**: Reduce date range or disable auto-refresh

### Debug Mode
Enable developer mode in Odoo to see detailed error messages in browser console.

### Logs
Check Odoo logs for controller errors:
```bash
tail -f /var/log/odoo/odoo.log | grep "hr_analytics"
```

## Development

### Adding New Metrics
1. Add computed fields to `hr.employee` or `hr.analytics.stats`
2. Update controller to include new data
3. Modify frontend templates and charts

### Customizing Charts
Charts are rendered using Chart.js. Modify the chart configuration in `dashboard.js`:
```javascript
get customChartData() {
    return {
        labels: [...],
        datasets: [{...}]
    };
}
```

## Version History

- **1.0.0**: Initial release with core dashboard functionality
  - Real-time metrics and charts
  - Department filtering
  - PDF export capability
  - Auto-refresh functionality
  - Performance optimizations
  - Comprehensive error handling

## Support

For issues and feature requests, please contact your system administrator or check the module documentation.
