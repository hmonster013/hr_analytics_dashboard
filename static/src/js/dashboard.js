/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { ChartRenderer } from "./chart_renderer";

class NumberCard extends Component {
    static template = "hr_analytics_dashboard.NumberCard";
    static props = { 
        title: String, 
        value: [String, Number],
        icon: { type: String, optional: true },
        color: { type: String, optional: true },
        onClick: { type: Function, optional: true }
    };
}

class FilterSection extends Component {
    static template = "hr_analytics_dashboard.FilterSection";
    static props = { 
        departments: Array,
        selectedDepartment: [String, Number],
        startDate: String,
        endDate: String,
        onFilterChange: Function
    };
}

class HRDashboard extends Component {
    static template = "hr_analytics_dashboard.Dashboard";
    static components = { NumberCard, ChartRenderer, FilterSection };

    setup() {
        this.state = useState({ 
            data: {},
            loading: true,
            error: null,
            filters: {
                department_id: null,
                start_date: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0], // First day of current month
                end_date: new Date().toISOString().split('T')[0] // Today
            },
            departments: [],
            autoRefresh: true, // Auto-refresh enabled by default
            lastUpdated: null,
            isRefreshing: false
        });

        this.actionService = useService("action");
        this.refreshInterval = null;
        this.loadData();
        this.loadDepartments();
        this.startAutoRefresh();
    }

    async loadData() {
        this.state.loading = !this.state.lastUpdated; // Only show loading on first load
        this.state.isRefreshing = !!this.state.lastUpdated; // Show refreshing indicator for subsequent loads
        try {
            console.log("Sending filters to API:", this.state.filters);
            const result = await rpc("/hr_analytics/data", this.state.filters);
            console.log("Received data from API:", result);
            this.state.data = result;
            this.state.loading = false;
            this.state.isRefreshing = false;
            this.state.lastUpdated = new Date();
            this.state.error = null;
        } catch (error) {
            console.error("API Error:", error);
            this.state.error = "Không thể lấy dữ liệu dashboard";
            this.state.loading = false;
            this.state.isRefreshing = false;
        }
    }

    async loadDepartments() {
        try {
            const departments = await rpc("/web/dataset/call_kw", {
                model: "hr.department",
                method: "search_read",
                args: [[], ["id", "name"]],
                kwargs: {}
            });
            this.state.departments = departments;
            console.log("Loaded departments:", departments);
        } catch (error) {
            console.error("Failed to load departments:", error);
        }
    }

    onFilterChange(filterType, value) {
        console.log(`Filter changed: ${filterType} = ${value}`);
        this.state.filters[filterType] = value;
        console.log("Updated filters:", this.state.filters);
        this.loadData();
        
        // Restart auto-refresh when filters change
        if (this.state.autoRefresh) {
            this.startAutoRefresh();
        }
    }

    startAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        if (this.state.autoRefresh) {
            this.refreshInterval = setInterval(() => {
                if (!this.state.loading && !this.state.isRefreshing) {
                    this.loadData();
                }
            }, 30000); // Refresh every 30 seconds
        }
    }

    toggleAutoRefresh() {
        this.state.autoRefresh = !this.state.autoRefresh;
        
        if (this.state.autoRefresh) {
            this.startAutoRefresh();
            this.showNotification('success', 'Cập nhật tự động đã được bật (30 giây)');
        } else {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
                this.refreshInterval = null;
            }
            this.showNotification('info', 'Cập nhật tự động đã được tắt');
        }
    }

    manualRefresh() {
        if (!this.state.loading && !this.state.isRefreshing) {
            this.loadData();
            this.showNotification('info', 'Đang cập nhật dữ liệu...');
        }
    }

    willUnmount() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }

    // Navigation handlers
    onEmployeesClick() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Employees",
            res_model: "hr.employee",
            view_mode: "tree,form",
            views: [[false, "tree"], [false, "form"]],
            target: "current"
        });
    }

    onAttendanceClick() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Attendance",
            res_model: "hr.attendance",
            view_mode: "tree,form",
            views: [[false, "tree"], [false, "form"]],
            target: "current"
        });
    }

    onPayrollClick() {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Contracts",
            res_model: "hr.contract",
            view_mode: "tree,form",
            views: [[false, "tree"], [false, "form"]],
            target: "current"
        });
    }

    // Export to PDF functionality
    async exportToPDF() {
        try {
            // Show loading message
            const originalButton = document.querySelector('.export-pdf-btn');
            const originalText = originalButton.innerHTML;
            originalButton.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Đang xuất...';
            originalButton.disabled = true;

            // Load required libraries
            await this.loadExportLibraries();

            // Get the dashboard element
            const dashboard = document.querySelector('.o_hr_dashboard');
            if (!dashboard) {
                throw new Error('Không tìm thấy dashboard element');
            }

            // Store original styles
            const originalDashboardStyle = {
                height: dashboard.style.height,
                overflow: dashboard.style.overflow,
                overflowY: dashboard.style.overflowY
            };

            // Hide elements for PDF export
            const elementsToHide = [
                document.querySelector('.export-pdf-btn'),
                document.querySelector('.filter-section')
            ];

            const hiddenElements = [];
            elementsToHide.forEach(element => {
                if (element) {
                    hiddenElements.push({
                        element: element,
                        originalDisplay: element.style.display
                    });
                    element.style.display = 'none';
                }
            });

            // Adjust dashboard for full content capture
            dashboard.style.height = 'auto';
            dashboard.style.overflow = 'visible';
            dashboard.style.overflowY = 'visible';

            // Wait for charts to render completely
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Get the actual content height after adjustments
            const contentElement = dashboard.querySelector('div[style*="padding: 20px 16px"]');
            const actualHeight = contentElement ? contentElement.scrollHeight : dashboard.scrollHeight;
            const actualWidth = dashboard.scrollWidth;

            // Capture the dashboard as canvas with full content
            const canvas = await window.html2canvas(dashboard, {
                height: actualHeight,
                width: actualWidth,
                scrollX: 0,
                scrollY: 0,
                useCORS: true,
                allowTaint: true,
                scale: 1.5, // Good balance between quality and performance
                backgroundColor: '#f8fafc',
                logging: false,
                onclone: function(clonedDoc) {
                    // Ensure all content is visible in the cloned document
                    const clonedDashboard = clonedDoc.querySelector('.o_hr_dashboard');
                    if (clonedDashboard) {
                        clonedDashboard.style.height = 'auto';
                        clonedDashboard.style.overflow = 'visible';
                        clonedDashboard.style.overflowY = 'visible';
                    }
                }
            });

            // Restore original styles
            dashboard.style.height = originalDashboardStyle.height;
            dashboard.style.overflow = originalDashboardStyle.overflow;
            dashboard.style.overflowY = originalDashboardStyle.overflowY;

            // Show hidden elements again
            hiddenElements.forEach(item => {
                item.element.style.display = item.originalDisplay;
            });

            // Create PDF
            const { jsPDF } = window.jspdf;
            const pdf = new jsPDF({
                orientation: 'landscape',
                unit: 'mm',
                format: 'a4'
            });

            const imgData = canvas.toDataURL('image/png', 0.95);
            const pdfWidth = 297; // A4 landscape width
            const pdfHeight = 210; // A4 landscape height
            const imgWidth = pdfWidth;
            const imgHeight = (canvas.height * pdfWidth) / canvas.width;

            let heightLeft = imgHeight;
            let position = 0;

            // Add first page
            pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
            heightLeft -= pdfHeight;

            // Add additional pages if needed
            while (heightLeft >= 0) {
                position = heightLeft - imgHeight;
                pdf.addPage();
                pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
                heightLeft -= pdfHeight;
            }

            // Generate filename with current date and time
            const now = new Date();
            const dateStr = now.toISOString().split('T')[0];
            const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '-');
            const filename = `HR_Analytics_Dashboard_${dateStr}_${timeStr}.pdf`;

            // Save the PDF
            pdf.save(filename);

            // Restore button
            originalButton.innerHTML = originalText;
            originalButton.disabled = false;

            // Show success message
            this.showNotification('success', 'PDF đã được xuất thành công! Tất cả biểu đồ đã được bao gồm.');

        } catch (error) {
            console.error('Error exporting PDF:', error);
            
            // Restore button
            const button = document.querySelector('.export-pdf-btn');
            if (button) {
                button.innerHTML = '<i class="fa fa-file-pdf-o"></i> Xuất PDF';
                button.disabled = false;
                button.style.display = 'flex';
            }
            
            this.showNotification('error', 'Lỗi khi xuất PDF: ' + error.message);
        }
    }

    async loadExportLibraries() {
        // Load html2canvas
        if (!window.html2canvas) {
            await this.loadScript('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js');
        }
        
        // Load jsPDF
        if (!window.jspdf) {
            await this.loadScript('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js');
        }
    }

    loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    showNotification(type, message) {
        // Create notification element
        const notification = document.createElement('div');
        const colors = {
            success: '#10b981',
            error: '#ef4444',
            info: '#3b82f6'
        };
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 24px;
            border-radius: 12px;
            color: white;
            font-weight: 600;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            background: ${colors[type] || colors.info};
        `;
        
        const icons = {
            success: 'check',
            error: 'exclamation-triangle',
            info: 'info-circle'
        };
        
        notification.innerHTML = `
            <i class="fa fa-${icons[type] || icons.info}" style="margin-right: 8px;"></i>
            ${message}
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // Chart data formatters
    get attendanceChartData() {
        const trends = this.state.data.attendance_trends || [];
        return {
            labels: trends.map(item => new Date(item.date).toLocaleDateString('vi-VN')),
            datasets: [{
                label: "Giờ làm trung bình",
                data: trends.map(item => item.worked_hours),
                borderColor: "#6366f1",
                backgroundColor: "rgba(99, 102, 241, 0.1)",
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: "#6366f1",
                pointBorderColor: "#ffffff",
                pointBorderWidth: 2,
                pointRadius: 6
            }]
        };
    }

    get kpiDistributionData() {
        const dist = this.state.data.kpi_distribution || [];
        const colors = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#06b6d4"];
        return {
            labels: dist.map(item => `${item.score_range} điểm`),
            datasets: [{
                label: "Số lượng nhân viên",
                data: dist.map(item => item.count),
                backgroundColor: colors.slice(0, dist.length),
                borderWidth: 0,
                borderRadius: 8
            }]
        };
    }

    get salaryDistributionData() {
        const s = this.state.data.salary_distribution || [];
        const colors = ["#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"];
        return {
            labels: s.map(item => item.department),
            datasets: [{
                data: s.map(item => Math.round(item.total_salary / 1000000)),
                backgroundColor: colors.slice(0, s.length),
                borderWidth: 0,
                hoverOffset: 4
            }]
        };
    }

    get chartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        font: { size: 12 }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0,0,0,0.1)' },
                    ticks: { font: { size: 11 } }
                },
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 11 } }
                }
            }
        };
    }

    get pieChartOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        font: { size: 12 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.parsed} triệu VND`;
                        }
                    }
                }
            }
        };
    }
}

registry.category("actions").add("hr_analytics_dashboard.dashboard", HRDashboard);
