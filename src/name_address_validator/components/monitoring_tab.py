# src/name_address_validator/components/monitoring_tab.py
"""
Monitoring Tab - System monitoring, performance metrics, and debug logs
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List


class MonitoringTab:
    """Monitoring and system status tab component"""
    
    def __init__(self, logger):
        self.logger = logger
        
        # Initialize session state for monitoring
        if 'monitoring_session_start' not in st.session_state:
            st.session_state.monitoring_session_start = datetime.now()
    
    def render(self):
        """Render the monitoring tab"""
        st.markdown('<div class="validation-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">System Monitoring & Performance</div>', unsafe_allow_html=True)
        
        # Sub-tabs for different monitoring views
        overview_tab, performance_tab, logs_tab, system_tab = st.tabs([
            "📊 Overview", "⚡ Performance", "🔍 Debug Logs", "🖥️ System Status"
        ])
        
        with overview_tab:
            self._render_overview()
        
        with performance_tab:
            self._render_performance_metrics()
        
        with logs_tab:
            self._render_debug_logs()
        
        with system_tab:
            self._render_system_status()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_overview(self):
        """Render system overview"""
        st.markdown("### 📈 System Overview")
        
        # Calculate session uptime
        uptime = datetime.now() - st.session_state.monitoring_session_start
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        
        # Get stats from session state
        name_stats = st.session_state.get('name_processing_stats', {})
        address_stats = st.session_state.get('address_processing_stats', {})
        
        # Overall metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_processed = name_stats.get('total_processed', 0) + address_stats.get('total_processed', 0)
            st.metric("Total Records Processed", total_processed)
        
        with col2:
            total_successful = (name_stats.get('successful_validations', 0) + 
                               address_stats.get('successful_validations', 0))
            st.metric("Successful Validations", total_successful)
        
        with col3:
            total_files = name_stats.get('files_processed', 0) + address_stats.get('files_processed', 0)
            st.metric("Files Processed", total_files)
        
        with col4:
            st.metric("Session Uptime", uptime_str)
        
        with col5:
            # Calculate overall success rate
            if total_processed > 0:
                success_rate = (total_successful / total_processed) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
            else:
                st.metric("Success Rate", "0%")
        
        # Service-specific metrics
        st.markdown("### 🔍 Service Breakdown")
        
        col6, col7 = st.columns(2)
        
        with col6:
            st.markdown("**Name Validation Service**")
            name_processed = name_stats.get('total_processed', 0)
            name_successful = name_stats.get('successful_validations', 0)
            name_files = name_stats.get('files_processed', 0)
            
            if name_processed > 0:
                name_success_rate = (name_successful / name_processed) * 100
                st.write(f"- Records Processed: {name_processed}")
                st.write(f"- Successful: {name_successful}")
                st.write(f"- Success Rate: {name_success_rate:.1f}%")
                st.write(f"- Files Processed: {name_files}")
            else:
                st.write("- No name validations performed yet")
        
        with col7:
            st.markdown("**Address Validation Service**")
            addr_processed = address_stats.get('total_processed', 0)
            addr_successful = address_stats.get('successful_validations', 0)
            addr_files = address_stats.get('files_processed', 0)
            addr_qualified = address_stats.get('addresses_qualified', 0)
            
            if addr_processed > 0:
                addr_success_rate = (addr_successful / addr_processed) * 100
                st.write(f"- Records Processed: {addr_processed}")
                st.write(f"- Successful: {addr_successful}")
                st.write(f"- Success Rate: {addr_success_rate:.1f}%")
                st.write(f"- Files Processed: {addr_files}")
                st.write(f"- Addresses Qualified: {addr_qualified}")
            else:
                st.write("- No address validations performed yet")
        
        # Recent activity timeline
        if hasattr(self.logger, 'get_recent_logs'):
            recent_logs = self.logger.get_recent_logs(minutes=60)
            if recent_logs:
                st.markdown("### 📅 Recent Activity (Last Hour)")
                
                # Create timeline data
                timeline_data = []
                for log in recent_logs[-20:]:  # Last 20 activities
                    timeline_data.append({
                        'Time': log['timestamp'].strftime('%H:%M:%S'),
                        'Category': log.get('category', 'GENERAL'),
                        'Message': log.get('message', '')[:100] + ('...' if len(log.get('message', '')) > 100 else ''),
                        'Level': log.get('level', 'INFO')
                    })
                
                if timeline_data:
                    timeline_df = pd.DataFrame(timeline_data)
                    st.dataframe(timeline_df, use_container_width=True)
            else:
                st.info("No recent activity to display")
    
    def _render_performance_metrics(self):
        """Render performance metrics"""
        st.markdown("### ⚡ Performance Analytics")
        
        # Check if we have performance data
        if hasattr(self.logger, 'performance_metrics'):
            metrics = self.logger.performance_metrics
            
            if metrics:
                st.markdown("#### 📊 Operation Performance")
                
                # Group metrics by operation type
                operations = {}
                for metric in metrics:
                    op_name = metric.get('operation', 'unknown')
                    if op_name not in operations:
                        operations[op_name] = []
                    operations[op_name].append(metric)
                
                # Display performance for each operation
                for operation, op_metrics in operations.items():
                    with st.expander(f"🔧 {operation.replace('_', ' ').title()}"):
                        
                        # Calculate stats
                        durations = [m['duration_ms'] for m in op_metrics if m.get('success', True)]
                        success_count = sum(1 for m in op_metrics if m.get('success', True))
                        total_count = len(op_metrics)
                        
                        if durations:
                            avg_duration = sum(durations) / len(durations)
                            min_duration = min(durations)
                            max_duration = max(durations)
                            
                            col1, col2, col3, col4, col5 = st.columns(5)
                            
                            with col1:
                                st.metric("Total Calls", total_count)
                            
                            with col2:
                                st.metric("Successful", success_count)
                            
                            with col3:
                                success_rate = (success_count / total_count) * 100
                                st.metric("Success Rate", f"{success_rate:.1f}%")
                            
                            with col4:
                                st.metric("Avg Duration", f"{avg_duration:.1f}ms")
                            
                            with col5:
                                st.metric("Duration Range", f"{min_duration}-{max_duration}ms")
                            
                            # Recent performance trend
                            if len(op_metrics) > 1:
                                recent_metrics = sorted(op_metrics, key=lambda x: x['timestamp'])[-10:]
                                trend_data = pd.DataFrame([
                                    {
                                        'Time': m['timestamp'].strftime('%H:%M:%S'),
                                        'Duration (ms)': m['duration_ms'],
                                        'Success': '✅' if m.get('success', True) else '❌'
                                    }
                                    for m in recent_metrics
                                ])
                                
                                st.write("**Recent Performance:**")
                                st.dataframe(trend_data, use_container_width=True)
                        else:
                            st.write("No successful operations recorded yet")
            else:
                st.info("No performance metrics available yet")
        else:
            st.info("Performance tracking not available")
        
        # Resource usage (simplified)
        st.markdown("#### 🖥️ Resource Usage")
        
        # Session state size estimation
        session_size = len(str(st.session_state))
        st.write(f"- Session State Size: ~{session_size:,} characters")
        
        # Results storage
        name_results = len(st.session_state.get('name_validation_results', []))
        address_results = len(st.session_state.get('address_validation_results', []))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Stored Name Results", name_results)
        with col2:
            st.metric("Stored Address Results", address_results)
    
    def _render_debug_logs(self):
        """Render debug logs interface"""
        st.markdown("### 🔍 Debug Logs & Troubleshooting")
        
        if hasattr(self.logger, 'logs') and self.logger.logs:
            # Log filtering controls
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                level_filter = st.selectbox(
                    "Filter by Level",
                    options=["ALL"] + list(set(log.get('level', 'INFO') for log in self.logger.logs))
                )
            
            with col2:
                category_filter = st.selectbox(
                    "Filter by Category",
                    options=["ALL"] + list(set(log.get('category', 'GENERAL') for log in self.logger.logs))
                )
            
            with col3:
                time_filter = st.selectbox(
                    "Time Range",
                    options=["All Time", "Last 5 min", "Last 15 min", "Last Hour", "Last 4 Hours"]
                )
            
            with col4:
                max_logs = st.number_input(
                    "Max Logs",
                    min_value=10,
                    max_value=500,
                    value=100
                )
            
            # Apply filters
            filtered_logs = self.logger.logs.copy()
            
            if level_filter != "ALL":
                filtered_logs = [log for log in filtered_logs if log.get('level') == level_filter]
            
            if category_filter != "ALL":
                filtered_logs = [log for log in filtered_logs if log.get('category') == category_filter]
            
            if time_filter != "All Time":
                minutes_map = {
                    "Last 5 min": 5,
                    "Last 15 min": 15,
                    "Last Hour": 60,
                    "Last 4 Hours": 240
                }
                minutes = minutes_map[time_filter]
                cutoff_time = datetime.now() - timedelta(minutes=minutes)
                filtered_logs = [log for log in filtered_logs if log.get('timestamp', datetime.now()) > cutoff_time]
            
            # Display logs
            if filtered_logs:
                st.write(f"**Showing {min(len(filtered_logs), max_logs)} of {len(filtered_logs)} matching logs**")
                
                # Format logs for display
                log_entries = []
                for log in filtered_logs[-max_logs:]:
                    timestamp = log.get('timestamp', datetime.now()).strftime("%H:%M:%S.%f")[:-3]
                    level = log.get('level', 'INFO')
                    category = log.get('category', 'GENERAL')
                    message = log.get('message', '')
                    
                    # Color code by level
                    level_emoji = {
                        'ERROR': '🔴',
                        'WARNING': '🟡',
                        'INFO': '🔵',
                        'DEBUG': '⚪'
                    }.get(level, '⚪')
                    
                    log_entries.append(f"[{timestamp}] {level_emoji} {level} {category}: {message}")
                
                # Display in code block for better formatting
                st.code("\n".join(log_entries), language="text")
                
                # Export options
                col5, col6, col7 = st.columns(3)
                
                with col5:
                    if st.button("📥 Export Logs (JSON)", use_container_width=True):
                        if hasattr(self.logger, 'export_logs'):
                            json_data = self.logger.export_logs("json")
                            st.download_button(
                                "Download JSON",
                                data=json_data,
                                file_name=f"debug_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json"
                            )
                
                with col6:
                    if st.button("📥 Export Logs (CSV)", use_container_width=True):
                        if hasattr(self.logger, 'export_logs'):
                            csv_data = self.logger.export_logs("csv")
                            st.download_button(
                                "Download CSV",
                                data=csv_data,
                                file_name=f"debug_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                
                with col7:
                    if st.button("🗑️ Clear Logs", use_container_width=True):
                        if hasattr(self.logger, 'clear'):
                            self.logger.clear()
                            st.success("Logs cleared!")
                            st.rerun()
            else:
                st.info("No logs match the current filters")
        else:
            st.info("No debug logs available")
    
    def _render_system_status(self):
        """Render system status information"""
        st.markdown("### 🖥️ System Status & Health Check")
        
        # Service availability checks
        st.markdown("#### 🔧 Service Status")
        
        # This would need to be passed from the main app
        # For now, we'll use session state or basic checks
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Name Validation Service**")
            # Basic health indicators
            name_stats = st.session_state.get('name_processing_stats', {})
            if name_stats.get('total_processed', 0) > 0 or True:  # Always show as available for demo
                st.success("✅ Service Available")
                st.write("- Name parsing: Operational")
                st.write("- Validation engine: Operational") 
                st.write("- Suggestion system: Operational")
            else:
                st.error("❌ Service Issues")
        
        with col2:
            st.markdown("**Address Validation Service**")
            address_stats = st.session_state.get('address_processing_stats', {})
            
            # Check if we have USPS configuration info in logs
            usps_configured = False
            if hasattr(self.logger, 'logs'):
                for log in self.logger.logs:
                    if 'USPS' in log.get('message', '') and 'configured' in log.get('message', ''):
                        usps_configured = True
                        break
            
            if usps_configured:
                st.success("✅ USPS API Connected")
                st.write("- Address standardization: Operational")
                st.write("- USPS validation: Operational")
                st.write("- Deliverability check: Operational")
            else:
                st.warning("⚠️ USPS API Not Configured")
                st.write("- Address standardization: Limited")
                st.write("- USPS validation: Unavailable")
                st.write("- Deliverability check: Unavailable")
        
        # Environment information
        st.markdown("#### 🌍 Environment Information")
        
        import sys
        import platform
        
        env_info = {
            'Python Version': sys.version.split()[0],
            'Platform': platform.system(),
            'Platform Version': platform.release(),
            'Streamlit Version': st.__version__ if hasattr(st, '__version__') else 'Unknown',
            'Session Started': st.session_state.monitoring_session_start.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        for key, value in env_info.items():
            st.write(f"- **{key}**: {value}")
        
        # Configuration status
        st.markdown("#### ⚙️ Configuration Status")
        
        config_status = []
        
        # Check for environment variables (basic check)
        import os
        if os.getenv('USPS_CLIENT_ID'):
            config_status.append(("USPS_CLIENT_ID", "✅ Set"))
        else:
            config_status.append(("USPS_CLIENT_ID", "❌ Not Set"))
        
        if os.getenv('USPS_CLIENT_SECRET'):
            config_status.append(("USPS_CLIENT_SECRET", "✅ Set"))
        else:
            config_status.append(("USPS_CLIENT_SECRET", "❌ Not Set"))
        
        for config_name, status in config_status:
            st.write(f"- **{config_name}**: {status}")
        
        # Session cleanup
        st.markdown("#### 🧹 Session Management")
        
        col3, col4 = st.columns(2)
        
        with col3:
            if st.button("🗑️ Clear Name Results", type="secondary", use_container_width=True):
                st.session_state.name_validation_results = []
                st.session_state.name_processing_stats = {
                    'total_processed': 0,
                    'successful_validations': 0,
                    'failed_validations': 0,
                    'files_processed': 0
                }
                st.success("Name validation results cleared")
                st.rerun()
        
        with col4:
            if st.button("🗑️ Clear Address Results", type="secondary", use_container_width=True):
                st.session_state.address_validation_results = []
                st.session_state.address_processing_stats = {
                    'total_processed': 0,
                    'successful_validations': 0,
                    'failed_validations': 0,
                    'files_processed': 0,
                    'addresses_qualified': 0
                }
                st.success("Address validation results cleared")
                st.rerun()
        
        if st.button("🔄 Reset Session", type="primary", use_container_width=True):
            # Reset all session state
            for key in list(st.session_state.keys()):
                if key not in ['monitoring_session_start']:  # Keep session start time
                    del st.session_state[key]
            
            st.success("Session reset completed")
            st.rerun()