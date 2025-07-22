/** @odoo-module **/

import { Component, useRef, onMounted, onWillStart } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class ChartRenderer extends Component {
    static template = "hr_analytics_dashboard.ChartRenderer";
    static props = {
        type: { type: String, optional: true },
        data: Object,
        options: { type: Object, optional: true }
    };

    setup() {
        this.chartRef = useRef("chart");
        this.chartInstance = null;
        this.chartLoaded = false;
        
        onWillStart(async () => {
            try {
                // Try different Chart.js paths for Odoo 18
                await loadJS("/web/static/lib/chart/chart.js");
                this.chartLoaded = true;
                console.log("Chart.js loaded successfully");
            } catch (error) {
                console.warn("Failed to load Chart.js from /web/static/lib/chart/chart.js, trying alternative path");
                try {
                    await loadJS("/web/static/lib/Chart/Chart.js");
                    this.chartLoaded = true;
                    console.log("Chart.js loaded from alternative path");
                } catch (error2) {
                    console.error("Failed to load Chart.js:", error2);
                    this.chartLoaded = false;
                }
            }
        });
        
        onMounted(() => {
            if (this.chartLoaded) {
                this.renderChart();
            } else {
                this.showError();
            }
        });
    }

    renderChart() {
        if (!window.Chart) {
            console.error("Chart.js is not available");
            this.showError();
            return;
        }

        // Destroy chart cũ nếu có
        if (this.chartInstance) {
            this.chartInstance.destroy();
        }
        
        const { type, data, options } = this.props;
        try {
            this.chartInstance = new window.Chart(this.chartRef.el.getContext('2d'), {
                type: type || "bar",
                data: data,
                options: { responsive: true, maintainAspectRatio: false, ...options }
            });
        } catch (error) {
            console.error("Error creating chart:", error);
            this.showError();
        }
    }

    showError() {
        if (this.chartRef.el) {
            this.chartRef.el.style.display = 'none';
            const errorDiv = document.createElement('div');
            errorDiv.innerHTML = '<p style="color: red; text-align: center;">Chart library not available</p>';
            this.chartRef.el.parentNode.appendChild(errorDiv);
        }
    }
}
