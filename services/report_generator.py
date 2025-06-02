"""
Comprehensive Report Generator for FloodScope AI
Generates detailed flood analysis reports in multiple formats
"""

import streamlit as st
from datetime import datetime
import json
from typing import Dict, Any, Optional
import base64

class ReportGenerator:
    """Generate comprehensive flood analysis reports"""
    
    def __init__(self):
        """Initialize the report generator"""
        pass
    
    def generate_flood_analysis_report(self, 
                                     location_data: Dict[str, Any],
                                     analysis_results: Dict[str, Any],
                                     weather_data: Optional[Dict[str, Any]] = None,
                                     satellite_data: Optional[Dict[str, Any]] = None) -> str:
        """Generate a comprehensive flood analysis report"""
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')
        location_name = location_data.get('name', 'Unknown Location')
        coordinates = f"({location_data.get('lat', 0):.4f}, {location_data.get('lon', 0):.4f})"
        
        report = f"""# FloodScope AI - Flood Analysis Report

**Location:** {location_name} {coordinates}  
**Analysis Date:** {timestamp}  
**Report ID:** FSA-{datetime.now().strftime('%Y%m%d%H%M%S')}

---

## Executive Summary

"""
        
        # Add flood risk assessment
        if analysis_results:
            risk_level = analysis_results.get('statistics', {}).get('overall_risk', 'Unknown')
            affected_area = analysis_results.get('statistics', {}).get('total_flood_area_km2', 0)
            confidence = analysis_results.get('mean_confidence', 0) * 100
            
            report += f"""**Overall Flood Risk:** {risk_level.upper()}  
**Affected Area:** {affected_area:.2f} km²  
**Detection Confidence:** {confidence:.1f}%  
**Analysis Method:** Satellite imagery with weather validation

"""
            
            # Risk interpretation
            if risk_level.lower() == 'severe':
                report += "🔴 **SEVERE RISK**: Immediate attention required. Evacuation may be necessary.\n\n"
            elif risk_level.lower() == 'high':
                report += "🟠 **HIGH RISK**: Significant flood conditions detected. Monitor closely.\n\n"
            elif risk_level.lower() == 'moderate':
                report += "🟡 **MODERATE RISK**: Elevated flood conditions. Exercise caution.\n\n"
            else:
                report += "🟢 **LOW RISK**: Current conditions show minimal flood threat.\n\n"
        
        # Weather conditions
        if weather_data:
            report += "## Current Weather Conditions\n\n"
            
            temp = weather_data.get('temperature', 'N/A')
            humidity = weather_data.get('humidity', 'N/A')
            rain_current = weather_data.get('current_rain', 0)
            rain_24h = weather_data.get('rain_24h', 0)
            pressure = weather_data.get('pressure', 'N/A')
            wind_speed = weather_data.get('wind_speed', 'N/A')
            condition = weather_data.get('weather_condition', 'N/A')
            
            report += f"""- **Temperature:** {temp}°C
- **Humidity:** {humidity}%
- **Current Rainfall:** {rain_current} mm/h
- **24-Hour Rainfall:** {rain_24h} mm
- **Atmospheric Pressure:** {pressure} hPa
- **Wind Speed:** {wind_speed} m/s
- **Weather Condition:** {condition}

"""
            
            # Rainfall assessment
            if rain_24h > 50:
                report += "⚠️ **Heavy Rainfall Warning**: Significant precipitation increases flood risk.\n\n"
            elif rain_24h > 20:
                report += "⚠️ **Moderate Rainfall**: Elevated precipitation levels detected.\n\n"
        
        # Satellite analysis details
        if satellite_data:
            report += "## Satellite Analysis\n\n"
            
            sensor_type = satellite_data.get('sensor_type', 'Unknown')
            acquisition_date = satellite_data.get('acquisition_date', 'Unknown')
            cloud_cover = satellite_data.get('cloud_cover_percentage', 0)
            
            report += f"""- **Satellite Sensor:** {sensor_type}
- **Image Acquisition:** {acquisition_date}
- **Cloud Cover:** {cloud_cover:.1f}%
- **Processing Method:** Advanced machine learning flood detection

"""
            
            if cloud_cover > 70:
                report += "☁️ **Note**: High cloud cover may limit optical satellite accuracy. Radar data recommended.\n\n"
        
        # Detailed flood analysis
        if analysis_results and 'flood_regions' in analysis_results:
            flood_regions = analysis_results['flood_regions']
            if flood_regions:
                report += f"## Flood Detection Details\n\n"
                report += f"**Number of Flood Regions Detected:** {len(flood_regions)}\n\n"
                
                for i, region in enumerate(flood_regions[:5], 1):  # Show first 5 regions
                    area = region.get('area_km2', 0)
                    confidence = region.get('confidence', 0) * 100
                    severity = region.get('severity', 'Unknown')
                    
                    report += f"**Region {i}:**\n"
                    report += f"- Area: {area:.3f} km²\n"
                    report += f"- Confidence: {confidence:.1f}%\n"
                    report += f"- Severity: {severity}\n\n"
        
        # Safety recommendations
        report += "## Safety Recommendations\n\n"
        
        if analysis_results:
            risk_level = analysis_results.get('statistics', {}).get('overall_risk', 'low')
            
            if risk_level.lower() in ['severe', 'high']:
                report += """### Immediate Actions Required

1. **Monitor Official Alerts**: Stay tuned to emergency services and weather warnings
2. **Avoid Flood Areas**: Do not drive or walk through flooded roads
3. **Emergency Preparedness**: Ensure emergency kit is ready and accessible
4. **Evacuation Readiness**: Be prepared to evacuate if advised by authorities
5. **Communication**: Keep charged phone and inform family of your status

### Emergency Contacts
- Local Emergency Services: 112 (India)
- Disaster Management: Contact local district collector
- Weather Updates: India Meteorological Department

"""
            else:
                report += """### General Precautions

1. **Stay Informed**: Monitor weather forecasts and flood warnings
2. **Avoid Risk Areas**: Stay away from rivers, streams, and low-lying areas
3. **Emergency Kit**: Keep basic emergency supplies readily available
4. **Travel Planning**: Check conditions before traveling to flood-prone areas
5. **Communication**: Maintain contact with family and local authorities

"""
        
        # Technical details
        report += "## Technical Analysis Details\n\n"
        
        if analysis_results:
            statistics = analysis_results.get('statistics', {})
            
            report += f"""### Detection Metrics
- **Total Analyzed Area:** {statistics.get('total_area_km2', 0):.2f} km²
- **Flood Area Detected:** {statistics.get('total_flood_area_km2', 0):.2f} km²
- **Flood Percentage:** {statistics.get('flood_percentage', 0):.2f}%
- **Mean Detection Confidence:** {analysis_results.get('mean_confidence', 0)*100:.1f}%

### Processing Information
- **Analysis Method:** {analysis_results.get('detection_method', 'Multi-spectral analysis')}
- **Sensor Data:** {analysis_results.get('sensor_type', 'Satellite imagery')}
- **Processing Time:** {analysis_results.get('processing_time', 'Unknown')}

"""
        
        # Data sources and limitations
        report += """## Data Sources & Limitations

### Data Sources
- **Satellite Imagery**: Sentinel-1 (Radar) and Sentinel-2 (Optical)
- **Weather Data**: Real-time meteorological services
- **Flood Detection**: Advanced machine learning algorithms
- **Ground Truth**: Weather station and sensor network data

### Important Limitations
- Satellite imagery may be affected by cloud cover
- Detection accuracy varies with terrain and urban density
- Real-time conditions may change rapidly
- This analysis supplements but does not replace official emergency warnings

### Recommendations for Use
- Always cross-reference with official weather and emergency services
- Use as part of comprehensive flood risk assessment
- Consider local knowledge and ground conditions
- Update analysis regularly during active weather events

---

## Disclaimer

This automated flood analysis is provided for informational purposes only. FloodScope AI uses advanced satellite imagery and machine learning for flood detection, but results should always be verified with official emergency services and local authorities.

**For emergency situations, contact local emergency services immediately.**

Report generated by FloodScope AI - Advanced Flood Detection System  
© 2024 FloodScope AI. All rights reserved.

---

*This report was automatically generated on {timestamp}*
"""
        
        return report
    
    def generate_comparison_report(self, analyses: list) -> str:
        """Generate a comparison report of multiple analyses"""
        
        if not analyses:
            return "No analyses available for comparison."
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')
        
        report = f"""# FloodScope AI - Comparative Analysis Report

**Generated:** {timestamp}  
**Number of Analyses:** {len(analyses)}  
**Report Type:** Multi-temporal Flood Comparison

---

## Analysis Overview

"""
        
        for i, analysis in enumerate(analyses, 1):
            location = analysis.get('location', {}).get('name', f'Location {i}')
            date = analysis.get('timestamp', 'Unknown')
            risk = analysis.get('results', {}).get('statistics', {}).get('overall_risk', 'Unknown')
            area = analysis.get('results', {}).get('statistics', {}).get('total_flood_area_km2', 0)
            
            report += f"""### Analysis {i}: {location}
- **Date:** {date}
- **Risk Level:** {risk}
- **Affected Area:** {area:.2f} km²

"""
        
        # Trend analysis
        report += "## Trend Analysis\n\n"
        
        if len(analyses) > 1:
            areas = [a.get('results', {}).get('statistics', {}).get('total_flood_area_km2', 0) for a in analyses]
            
            if areas[0] < areas[-1]:
                trend = "increasing"
                direction = "⬆️"
            elif areas[0] > areas[-1]:
                trend = "decreasing"
                direction = "⬇️"
            else:
                trend = "stable"
                direction = "➡️"
            
            report += f"""**Flood Area Trend:** {direction} {trend.title()}

The analysis shows flood conditions are **{trend}** over the analyzed period.

"""
        
        report += """---

*Comparative analysis helps identify trends and patterns in flood conditions over time.*
"""
        
        return report
    
    def create_download_button(self, report_content: str, filename: str, label: str = "Download Report"):
        """Create a download button for the report"""
        
        # Create download button
        st.download_button(
            label=f"📄 {label}",
            data=report_content.encode('utf-8'),
            file_name=filename,
            mime="text/markdown",
            help="Download the complete analysis report"
        )
    
    def create_pdf_download(self, report_content: str, filename: str):
        """Create PDF download option (basic HTML conversion)"""
        
        # Convert markdown to basic HTML for PDF-like formatting
        html_content = f"""
        <html>
        <head>
            <title>FloodScope AI Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #1f77b4; }}
                h2 {{ color: #ff7f0e; }}
                h3 {{ color: #2ca02c; }}
                .warning {{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; }}
                .error {{ background-color: #f8d7da; padding: 10px; border-left: 4px solid #dc3545; }}
                .success {{ background-color: #d4edda; padding: 10px; border-left: 4px solid #28a745; }}
            </style>
        </head>
        <body>
            <pre>{report_content}</pre>
        </body>
        </html>
        """
        
        st.download_button(
            label="📋 Download as HTML",
            data=html_content.encode('utf-8'),
            file_name=filename.replace('.md', '.html'),
            mime="text/html",
            help="Download report as HTML file"
        )
    
    def generate_summary_stats(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics for the analysis"""
        
        stats = {}
        
        if analysis_data and 'results' in analysis_data:
            results = analysis_data['results']
            statistics = results.get('statistics', {})
            
            stats = {
                'total_area': statistics.get('total_area_km2', 0),
                'flood_area': statistics.get('total_flood_area_km2', 0),
                'flood_percentage': statistics.get('flood_percentage', 0),
                'risk_level': statistics.get('overall_risk', 'Unknown'),
                'confidence': results.get('mean_confidence', 0) * 100,
                'regions_detected': len(results.get('flood_regions', [])),
                'sensor_type': results.get('sensor_type', 'Unknown'),
                'analysis_timestamp': analysis_data.get('timestamp', datetime.now())
            }
        
        return stats