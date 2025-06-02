import streamlit as st
import folium
from streamlit_folium import st_folium
import os
import numpy as np
from PIL import Image
import io
import tempfile
import datetime
import pandas as pd
import matplotlib.pyplot as plt

# Load environment variables
from load_env import load_environment

from utils.geocoding import geocode_location
from utils.sentinel_hub import get_sentinel_image
from utils.flood_detection import detect_floods
from utils.chat import (initialize_chat_history, update_chat_context, 
                      display_chat, generate_flood_report)
from utils.save_results import save_analysis_results, load_analysis_history, get_analysis_details
from utils.verification import verify_flood_event, add_verification_to_report, get_verification_badge

# Set page config
st.set_page_config(
    page_title="Real-Time Flood Detection",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #424242;
        margin-top: 0;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #1565C0;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #E0E0E0;
    }
    .metric-container {
        background-color: #F5F7FA;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .info-box {
        background-color: #E3F2FD;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #2196F3;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #FFF8E1;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #FFC107;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #E8F5E9;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #4CAF50;
        margin-bottom: 1rem;
    }
    .map-container {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #E0E0E0;
    }
    .data-table {
        margin-top: 1rem;
    }
    .stButton button {
        background-color: #1976D2;
        color: white;
        font-weight: 500;
    }
    .stButton button:hover {
        background-color: #1565C0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for app navigation
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Analysis"
    
# Initialize history loading state
if 'load_from_history' not in st.session_state:
    st.session_state.load_from_history = False
if 'history_metadata' not in st.session_state:
    st.session_state.history_metadata = None
if 'history_satellite_image' not in st.session_state:
    st.session_state.history_satellite_image = None
if 'history_flood_mask' not in st.session_state:
    st.session_state.history_flood_mask = None

# Load environment variables
load_environment()

# App title and description
st.markdown('<h1 class="main-header">🌊 Real-Time Flood Detection</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Monitor, analyze, and predict flooding using satellite imagery and AI</p>', unsafe_allow_html=True)

# Sidebar for navigation and input parameters
with st.sidebar:
    st.header("Navigation")
    
    # Navigation tabs
    selected_tab = st.radio("Select view", ["Analysis", "History", "Historical Data", "Predictions", "Chat Assistant", "Report"], label_visibility="collapsed")
    st.session_state.current_tab = selected_tab
    
    st.markdown("---")
    
    st.header("Input Parameters")
    
    # Location input method selection
    input_method = st.radio("Select input method:", ["Location Name", "Coordinates"])
    
    if input_method == "Location Name":
        location_name = st.text_input("Enter location name (e.g., 'Mumbai'):")
        lat, lon = None, None
    else:
        location_name = None
        col1, col2 = st.columns(2)
        with col1:
            lat = st.number_input("Latitude:", value=19.076, format="%.4f", min_value=-90.0, max_value=90.0)
        with col2:
            lon = st.number_input("Longitude:", value=72.877, format="%.4f", min_value=-180.0, max_value=180.0)
    
    # Analysis parameters container
    with st.expander("Analysis Parameters", expanded=True):
        # Satellite selection
        satellite_option = st.radio("Satellite Selection:", [
            "Auto (Based on Cloud Coverage)", 
            "Sentinel-2 (Optical)", 
            "Sentinel-1 (Radar)"
        ])
        
        if satellite_option == "Auto (Based on Cloud Coverage)":
            auto_select = True
            preferred_satellite = None
            # Show cloud threshold only for auto mode
            cloud_threshold = st.slider("Cloud coverage threshold (%)", 0, 100, 20, 5,
                                      help="If cloud coverage exceeds this threshold, Sentinel-1 (radar) will be used")
        else:
            auto_select = False
            preferred_satellite = "sentinel-2" if "Optical" in satellite_option else "sentinel-1"
            cloud_threshold = 20  # Default, not used in manual mode
        
        # Date range options
        date_option = st.radio("Date Selection:", [
            "Latest Available", 
            "Custom Date Range",
            "Historical Comparison",
            "Time-Specific Analysis"
        ])
        
        if date_option == "Custom Date Range":
            custom_date_col1, custom_date_col2 = st.columns(2)
            with custom_date_col1:
                start_date = st.date_input("Start date", value=datetime.date.today() - datetime.timedelta(days=30))
            with custom_date_col2:
                end_date = st.date_input("End date", value=datetime.date.today())
        elif date_option == "Historical Comparison":
            start_date = st.date_input("Historical date", value=datetime.date.today() - datetime.timedelta(days=365))
        elif date_option == "Time-Specific Analysis":
            # Allow specifying both date and time for precise flood timing
            date_col, time_col = st.columns(2)
            with date_col:
                specific_date = st.date_input("Select date", value=datetime.date.today())
            with time_col:
                time_options = ["Morning (6AM-10AM)", "Midday (10AM-2PM)", "Afternoon (2PM-6PM)", "Evening (6PM-10PM)", "Night (10PM-6AM)"]
                specific_time = st.selectbox("Select time period", options=time_options)
                
            st.info("Time-specific analysis helps detect rapid flood events that occur within a single day, such as flash floods or sudden weather changes.")
            end_date = datetime.date.today()
            comparison_enabled = True
        else:
            start_date, end_date = None, None
            comparison_enabled = False
        
        # Model selection
        model_option = st.radio("AI Model Selection:", [
            "Ensemble (AI4Flood + Prithvi)",
            "Microsoft AI4Flood",
            "IBM Prithvi"
        ])
    
    # Run button with more prominent styling
    run_analysis = st.button("Run Flood Detection", type="primary", use_container_width=True)
    
    # Info about models
    with st.expander("About AI Models", expanded=False):
        st.markdown("""
        This application uses two advanced AI models:
        
        - **Microsoft AI4Flood**: Specialized flood detection model developed by Microsoft that excels at distinguishing between permanent water bodies and flood waters.
        
        - **IBM Prithvi**: Foundation model for earth observation that can generalize well across diverse conditions.
        
        - **Ensemble**: Combines both models for improved accuracy.
        """)
    
    # Info about Sentinel Hub API
    with st.expander("About Satellite Data", expanded=False):
        st.markdown("""
        This application uses:
        - **Sentinel-2**: Optical imagery (affected by clouds)
        - **Sentinel-1**: Radar imagery (works through clouds)
        
        Provided by the Sentinel Hub API.
        """)

# Initialize session state variables for results
if 'results' not in st.session_state:
    st.session_state.results = None
if 'coordinates' not in st.session_state:
    st.session_state.coordinates = None
if 'flood_image' not in st.session_state:
    st.session_state.flood_image = None
if 'location_info' not in st.session_state:
    st.session_state.location_info = None
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = []
if 'original_image' not in st.session_state:
    st.session_state.original_image = None
if 'report_text' not in st.session_state:
    st.session_state.report_text = None
if 'verification_data' not in st.session_state:
    st.session_state.verification_data = None

# Initialize chat history
initialize_chat_history()

# Process input and run analysis when the button is clicked
if run_analysis:
    try:
        with st.spinner("Processing your request..."):
            # Step 1: Get coordinates from location name or use provided coordinates
            if input_method == "Location Name" and location_name:
                st.markdown('<div class="info-box">Geocoding location: ' + location_name + '</div>', unsafe_allow_html=True)
                lat, lon, location_info = geocode_location(location_name)
                if not lat or not lon:
                    st.error("Unable to geocode this location. Please check the spelling or try coordinates instead.")
                    st.stop()
                st.session_state.location_info = location_info
                st.session_state.coordinates = (lat, lon)
            elif input_method == "Coordinates" and lat is not None and lon is not None:
                st.markdown(f'<div class="info-box">Using coordinates: Lat {lat}, Lon {lon}</div>', unsafe_allow_html=True)
                st.session_state.coordinates = (lat, lon)
                st.session_state.location_info = None
            else:
                st.error("Please provide a valid location name or coordinates.")
                st.stop()
            
            # Step 2: Get satellite imagery
            st.markdown('<div class="info-box">Fetching Sentinel satellite imagery...</div>', unsafe_allow_html=True)
            
            # Set parameters based on user selections
            kwargs = {
                "lat": lat,
                "lon": lon,
                "cloud_threshold": cloud_threshold,
                "start_date": start_date,
                "end_date": end_date,
                "auto_select": auto_select
            }
            
            if preferred_satellite:
                kwargs["preferred_satellite"] = preferred_satellite
                
            # Add time period parameter if using time-specific analysis
            if date_option == "Time-Specific Analysis" and 'specific_time' in locals():
                kwargs["time_period"] = specific_time
                st.markdown(f'<div class="info-box">Analyzing flood conditions during {specific_time}</div>', unsafe_allow_html=True)
                
            image_data, satellite_type, acquisition_date, cloud_percentage = get_sentinel_image(**kwargs)
            
            if image_data is None:
                st.error("Unable to retrieve suitable satellite imagery for this location. Try adjusting the parameters or selecting a different location.")
                st.stop()
            
            # Save the original satellite image
            with io.BytesIO() as output:
                image_data.save(output, format="PNG")
                st.session_state.original_image = output.getvalue()
            
            # Step 3: Run flood detection model based on user selection
            model_info = ""
            if model_option == "Microsoft AI4Flood":
                from utils.ai4flood_integration import detect_floods_with_ai4flood
                st.markdown('<div class="info-box">Running Microsoft AI4Flood detection model...</div>', unsafe_allow_html=True)
                flood_mask, flood_percentage, flood_metadata = detect_floods_with_ai4flood(image_data, location=(lat, lon))
                model_info = "Microsoft AI4Flood"
            elif model_option == "IBM Prithvi":
                from utils.prithvi_integration import detect_floods_with_prithvi
                st.markdown('<div class="info-box">Running IBM Prithvi detection model...</div>', unsafe_allow_html=True)
                flood_mask, flood_percentage, flood_metadata = detect_floods_with_prithvi(image_data, location=(lat, lon))
                model_info = "IBM Prithvi"
            else:
                # Default to ensemble
                from utils.ensemble_model import detect_floods_ensemble
                st.markdown('<div class="info-box">Running Ensemble AI detection model (AI4Flood + Prithvi)...</div>', unsafe_allow_html=True)
                flood_mask, flood_percentage, flood_metadata = detect_floods_ensemble(image_data, location=(lat, lon))
                model_info = "Ensemble (AI4Flood + Prithvi)"
            
            # Step 4: Save results to session state
            result_data = {
                "satellite_type": satellite_type,
                "acquisition_date": acquisition_date,
                "cloud_percentage": cloud_percentage,
                "flood_percentage": flood_percentage,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "model": model_info,
                "confidence": flood_metadata.get("confidence", 0.8),
                "permanent_water_percentage": flood_metadata.get("permanent_water_percentage", 0)
            }
            
            st.session_state.results = result_data
            
            # Add to historical data
            if date_option == "Historical Comparison":
                # For historical comparison, we store both current and historical data
                # Make sure start_date is not None before using strftime
                historical_date = start_date.strftime("%Y-%m-%d") if start_date else "One year ago"
                current_date = datetime.date.today().strftime("%Y-%m-%d")
                
                st.session_state.historical_data = [
                    {"date": historical_date, "flood_percentage": flood_percentage * 0.8},  # Historical (simulated)
                    {"date": current_date, "flood_percentage": flood_percentage}  # Current
                ]
            else:
                # For regular analysis, just add to the historical record
                st.session_state.historical_data.append({
                    "date": acquisition_date if acquisition_date else datetime.date.today().strftime("%Y-%m-%d"),
                    "flood_percentage": flood_percentage
                })
                
                # Keep only last 10 records
                st.session_state.historical_data = st.session_state.historical_data[-10:]
            
            # Convert the flood mask to an image for display
            if flood_mask is not None:
                # Check if flood_mask is already a PIL Image or a numpy array
                if isinstance(flood_mask, np.ndarray):
                    # Convert the binary mask to an RGBA image where flooded areas are blue and transparent elsewhere
                    height, width = flood_mask.shape
                    rgba_mask = np.zeros((height, width, 4), dtype=np.uint8)
                    rgba_mask[flood_mask == 1] = [0, 0, 255, 180]  # Blue with alpha
                    rgba_mask[flood_mask == 0] = [0, 0, 0, 0]  # Transparent
                    
                    # Convert numpy array to PIL Image
                    flood_image = Image.fromarray(rgba_mask, mode='RGBA')
                else:
                    # flood_mask is already a PIL Image, convert to RGBA with blue for flood
                    flood_array = np.array(flood_mask.convert('L'))
                    height, width = flood_array.shape
                    rgba_mask = np.zeros((height, width, 4), dtype=np.uint8)
                    rgba_mask[flood_array > 127] = [0, 0, 255, 180]  # Blue with alpha
                    rgba_mask[flood_array <= 127] = [0, 0, 0, 0]  # Transparent
                    
                    # Convert back to PIL Image
                    flood_image = Image.fromarray(rgba_mask, mode='RGBA')
                
                # Save the flood overlay image
                with io.BytesIO() as output:
                    flood_image.save(output, format="PNG")
                    st.session_state.flood_image = output.getvalue()
            
            # Generate a report
            if st.session_state.coordinates and st.session_state.results:
                location_display = st.session_state.location_info if st.session_state.location_info else "Custom Location"
                
                # Perform real-time verification of the flood event
                with st.spinner("Verifying flood event with external sources..."):
                    try:
                        # Use the location and date to verify against external sources
                        verification_data = verify_flood_event(
                            location=location_display,
                            coordinates=st.session_state.coordinates,
                            date=st.session_state.results["acquisition_date"]
                        )
                        
                        # Store verification data in session state
                        st.session_state.verification_data = verification_data
                        
                        # Generate report first without verification
                        base_report = generate_flood_report(
                            location_display,
                            st.session_state.coordinates,
                            st.session_state.results["satellite_type"],
                            st.session_state.results["acquisition_date"],
                            st.session_state.results["flood_percentage"],
                            st.session_state.results
                        )
                        
                        # Add verification information to the report
                        st.session_state.report_text = add_verification_to_report(
                            base_report, 
                            verification_data
                        )
                        
                    except Exception as e:
                        st.warning(f"Could not verify flood event: {str(e)}")
                        # Generate report without verification if verification fails
                        st.session_state.report_text = generate_flood_report(
                            location_display,
                            st.session_state.coordinates,
                            st.session_state.results["satellite_type"],
                            st.session_state.results["acquisition_date"],
                            st.session_state.results["flood_percentage"],
                            st.session_state.results
                        )
            
            # Update chat context with the latest data
            update_chat_context(
                location=location_info if location_info else "Custom Location",
                coordinates=st.session_state.coordinates,
                satellite_type=satellite_type,
                acquisition_date=acquisition_date,
                flood_percentage=flood_percentage,
                flood_data=result_data
            )
            
            # Save analysis results for history
            try:
                # Get the image data
                original_image_data = st.session_state.original_image
                flood_image_data = st.session_state.flood_image if 'flood_image' in st.session_state else None
                
                # Save the analysis results with verification data
                save_analysis_results(
                    location_name=location_info if location_info else "Custom Location",
                    coordinates=st.session_state.coordinates,
                    satellite_type=satellite_type,
                    acquisition_date=acquisition_date,
                    flood_percentage=flood_percentage,
                    model_name=result_data.get("model", "Ensemble"),
                    satellite_image=original_image_data,
                    flood_mask=flood_image_data,
                    verification_data=st.session_state.verification_data
                )
            except Exception as e:
                st.warning(f"Could not save analysis to history: {str(e)}")
            
            st.success("Analysis completed successfully!")
            
    except Exception as e:
        st.error(f"An error occurred during analysis: {str(e)}")

# Display content based on selected tab
if st.session_state.current_tab == "Analysis":
    # Main analysis view
    
    # If we have results, display them
    if st.session_state.results and st.session_state.coordinates and st.session_state.original_image:
        # Split the view into two columns
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown('<h2 class="section-header">Satellite Imagery & Flood Detection</h2>', unsafe_allow_html=True)
            
            # Display original satellite image with flood overlay
            st.markdown("### Satellite Image with Flood Detection")
            
            # Create a Folium map for the location
            lat, lon = st.session_state.coordinates
            m = folium.Map(location=[lat, lon], zoom_start=10, tiles="CartoDB positron")
            
            # Add a marker for the location
            folium.Marker(
                [lat, lon],
                popup="Analysis Location",
                icon=folium.Icon(color="red", icon="info-sign"),
            ).add_to(m)
            
            # Display the Folium map
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            st_folium(m, width=700, height=400)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display the satellite image with flood overlay
            flood_overlay_tab, original_tab = st.tabs(["Flood Detection Overlay", "Original Satellite Image"])
            
            with flood_overlay_tab:
                # Display original image
                st.image(st.session_state.original_image, caption="Satellite Image", use_container_width=True)
                
                # Display flood overlay
                if st.session_state.flood_image:
                    st.image(st.session_state.flood_image, caption="Flood Detection Overlay", use_container_width=True)
            
            with original_tab:
                # Display only the original image
                st.image(st.session_state.original_image, caption="Original Satellite Image", use_container_width=True)
        
        with col2:
            st.markdown('<h2 class="section-header">Analysis Results</h2>', unsafe_allow_html=True)
            
            # Display the location info
            if st.session_state.location_info:
                st.markdown(f"**Location**: {st.session_state.location_info}")
            else:
                st.markdown(f"**Coordinates**: Lat: {lat:.4f}, Lon: {lon:.4f}")
            
            # Create metrics for the results
            results = st.session_state.results
            
            # Show verification status if available
            if st.session_state.verification_data:
                verification_badge = get_verification_badge(st.session_state.verification_data)
                st.markdown(f"**Verification Status:** {verification_badge}", unsafe_allow_html=True)
                
                # If there are recent reports, show them
                if st.session_state.verification_data.get("latest_reports"):
                    with st.expander("External Flood Reports", expanded=False):
                        for report in st.session_state.verification_data["latest_reports"]:
                            st.markdown(f"**{report['source']}**: {report['title']} ({report['date']})")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Flood Coverage", value=f"{results['flood_percentage']:.1f}%")
            with col2:
                st.metric(label="Confidence", value=f"{results['confidence']*100:.1f}%")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label="Cloud Coverage", value=f"{results['cloud_percentage']:.1f}%")
            with col2:
                st.metric(label="Date", value=results['acquisition_date'])
            
            # Create a severity indicator
            severity = "Low"
            severity_color = "#4CAF50"  # Green
            if results['flood_percentage'] >= 30:
                severity = "Severe"
                severity_color = "#F44336"  # Red
            elif results['flood_percentage'] >= 15:
                severity = "High"
                severity_color = "#FF9800"  # Orange
            elif results['flood_percentage'] >= 5:
                severity = "Moderate"
                severity_color = "#FFC107"  # Amber
            
            st.markdown(f"""
            <div style="margin-top: 1rem;">
                <h3 style="margin-bottom: 0.5rem;">Severity Assessment</h3>
                <div style="background-color: {severity_color}; color: white; padding: 1rem; border-radius: 5px; font-weight: bold; text-align: center; font-size: 1.2rem;">
                    {severity}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Analysis details
            st.markdown("### Analysis Details")
            st.markdown(f"""
            - **Satellite**: {results['satellite_type']}
            - **AI Model**: {results['model']}
            - **Analysis Time**: {results['timestamp']}
            """)
            
            # Interpretation and recommendations
            st.markdown("### Interpretation")
            if results['flood_percentage'] < 5:
                st.markdown("The analysis indicates minimal flooding in the area. This level of water coverage is likely within normal ranges for the region.")
            elif results['flood_percentage'] < 15:
                st.markdown("Moderate flooding detected. Some low-lying areas may be affected. Local waterways could be at elevated levels.")
            elif results['flood_percentage'] < 30:
                st.markdown("Significant flooding detected. Many low-lying areas are likely inundated. Evacuation may be necessary for some residents in affected areas.")
            else:
                st.markdown("Severe flooding detected. This represents a major flood event with potentially widespread impact. Immediate action may be required for safety.")
            
            st.markdown("### Recommendations")
            if results['flood_percentage'] < 5:
                st.markdown("""
                - Continue monitoring if precipitation is expected
                - No immediate action required
                """)
            elif results['flood_percentage'] < 15:
                st.markdown("""
                - Monitor water levels in rivers and streams
                - Avoid low-lying areas
                - Be prepared for possible evacuation in flood-prone zones
                """)
            elif results['flood_percentage'] < 30:
                st.markdown("""
                - Evacuate from low-lying and flood-affected areas
                - Follow guidance from local emergency services
                - Prepare for possible infrastructure disruptions
                """)
            else:
                st.markdown("""
                - Immediately evacuate from all flood-affected areas
                - Seek higher ground
                - Follow emergency protocols and official guidance
                - Prepare for significant infrastructure disruptions
                """)
            
    else:
        # Display instructions if no analysis has been run yet
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("### How to Use This Tool")
        st.markdown("""
        1. Enter a location name or coordinates in the sidebar
        2. Adjust analysis parameters if needed
        3. Click "Run Flood Detection" to analyze satellite imagery
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display a placeholder map centered on a default location
        st.markdown("### Interactive Map")
        default_map = folium.Map(location=[19.076, 72.877], zoom_start=2, tiles="CartoDB positron")
        st_folium(default_map, width=800, height=500)

elif st.session_state.current_tab == "Historical Data":
    # Historical data view
    st.markdown('<h2 class="section-header">Historical Flood Data</h2>', unsafe_allow_html=True)
    
    if not st.session_state.historical_data:
        st.markdown('<div class="info-box">No historical data available. Run an analysis first.</div>', unsafe_allow_html=True)
    else:
        # Create a DataFrame for the historical data
        df = pd.DataFrame(st.session_state.historical_data)
        
        # Create a time series plot
        st.markdown("### Flood Coverage Over Time")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df['date'], df['flood_percentage'], marker='o', linestyle='-', color='#1976D2')
        ax.set_xlabel('Date')
        ax.set_ylabel('Flood Coverage (%)')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_title('Flood Coverage Trend')
        
        # Add value annotations
        for i, row in df.iterrows():
            ax.annotate(f"{row['flood_percentage']:.1f}%", 
                        (row['date'], row['flood_percentage']),
                        textcoords="offset points",
                        xytext=(0, 10),
                        ha='center')
        
        st.pyplot(fig)
        
        # Display data table
        st.markdown("### Historical Data Records")
        st.markdown('<div class="data-table">', unsafe_allow_html=True)
        st.dataframe(df)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Download button for historical data
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Data as CSV",
            data=csv,
            file_name="flood_historical_data.csv",
            mime="text/csv",
        )

elif st.session_state.current_tab == "Predictions":
    # Predictions view
    st.markdown('<h2 class="section-header">Flood Predictions</h2>', unsafe_allow_html=True)
    
    if not st.session_state.results:
        st.markdown('<div class="info-box">No analysis data available. Run an analysis first to see predictions.</div>', unsafe_allow_html=True)
    else:
        # Get current flood data
        current_flood = st.session_state.results['flood_percentage']
        
        # Create simple prediction scenarios
        prediction_days = [1, 3, 7, 14]
        
        # Select prediction scenario
        scenario = st.radio(
            "Select scenario:",
            ["Receding Flood (Improving)", "Stable Conditions", "Worsening Conditions"],
            horizontal=True
        )
        
        # Generate prediction values based on scenario
        predictions = []
        
        if scenario == "Receding Flood (Improving)":
            factor = 0.8
            for day in prediction_days:
                predictions.append({
                    "day": day,
                    "value": max(0, current_flood * (factor ** day)),
                    "lower": max(0, current_flood * (factor ** day) * 0.8),
                    "upper": max(0, current_flood * (factor ** day) * 1.2)
                })
        elif scenario == "Stable Conditions":
            for day in prediction_days:
                predictions.append({
                    "day": day,
                    "value": current_flood,
                    "lower": max(0, current_flood * 0.9),
                    "upper": current_flood * 1.1
                })
        else:  # Worsening
            factor = 1.2
            for day in prediction_days:
                predictions.append({
                    "day": day,
                    "value": min(100, current_flood * (factor ** (day/2))),
                    "lower": min(100, current_flood * (factor ** (day/2)) * 0.8),
                    "upper": min(100, current_flood * (factor ** (day/2)) * 1.2)
                })
        
        # Create a DataFrame for predictions
        pred_df = pd.DataFrame(predictions)
        
        # Calculate dates for x-axis
        base_date = datetime.datetime.now()
        dates = [base_date + datetime.timedelta(days=day) for day in prediction_days]
        date_strings = [d.strftime("%Y-%m-%d") for d in dates]
        
        # Create prediction plot
        st.markdown("### Flood Coverage Prediction")
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot confidence interval
        ax.fill_between(date_strings, pred_df['lower'], pred_df['upper'], 
                        alpha=0.3, color='#1976D2', label='Confidence Interval')
        
        # Plot the main prediction line
        ax.plot(date_strings, pred_df['value'], marker='o', 
                linestyle='-', color='#1976D2', linewidth=2, label='Predicted Coverage')
        
        # Add current value
        ax.scatter([base_date.strftime("%Y-%m-%d")], [current_flood], 
                  color='#F44336', s=100, zorder=5, label='Current Coverage')
        
        # Set labels and title
        ax.set_xlabel('Date')
        ax.set_ylabel('Flood Coverage (%)')
        ax.set_title('Predicted Flood Coverage')
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        # Add value annotations
        ax.annotate(f"{current_flood:.1f}%", 
                    (base_date.strftime("%Y-%m-%d"), current_flood),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha='center')
        
        for i, row in pred_df.iterrows():
            ax.annotate(f"{row['value']:.1f}%", 
                        (date_strings[i], row['value']),
                        textcoords="offset points",
                        xytext=(0, 10),
                        ha='center')
        
        st.pyplot(fig)
        
        # Display prediction disclaimer
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("""
        **Disclaimer**: These predictions are simplified projections based on the selected scenario 
        and do not incorporate weather forecasts, terrain data, or hydrological modeling. 
        For accurate flood forecasting, please consult specialized hydrological services.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Prediction table
        st.markdown("### Prediction Data")
        table_data = []
        for i, row in pred_df.iterrows():
            table_data.append({
                "Date": date_strings[i],
                "Days from Now": prediction_days[i],
                "Predicted Coverage (%)": f"{row['value']:.1f}",
                "Lower Bound (%)": f"{row['lower']:.1f}",
                "Upper Bound (%)": f"{row['upper']:.1f}",
            })
        
        st.table(pd.DataFrame(table_data))

elif st.session_state.current_tab == "History":
    # History tab view
    st.markdown('<h2 class="section-header">Analysis History</h2>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">View and reload past flood analyses</p>', unsafe_allow_html=True)
    
    # Load analysis history
    history_df = load_analysis_history()
    
    if history_df is None or len(history_df) == 0:
        st.info("No saved analyses found. Run analyses in the Analysis tab to save results.")
    else:
        # Show a table of past analyses
        st.markdown("### Saved Analyses")
        
        # Reformat the dataframe for display
        columns_to_display = ['analysis_id', 'location', 'latitude', 'longitude', 
                             'satellite', 'acquisition_date', 'analysis_date', 
                             'flood_percentage', 'model']
        
        # Add verification columns if they exist
        if 'verified' in history_df.columns:
            columns_to_display.extend(['verified', 'verification_confidence'])
            
        display_df = history_df[columns_to_display].copy()
        
        # Rename columns for better display
        column_names = ['ID', 'Location', 'Latitude', 'Longitude', 
                        'Satellite', 'Image Date', 'Analysis Date', 
                        'Flood %', 'Model Used']
                        
        # Add verification column names if needed
        if 'verified' in history_df.columns:
            column_names.extend(['Verified', 'Verification Confidence'])
            
        display_df.columns = column_names
        
        # Format the flood percentage
        display_df['Flood %'] = display_df['Flood %'].apply(lambda x: f"{x:.2f}%")
        
        # Format verification columns if they exist
        if 'Verified' in display_df.columns:
            # Convert boolean to Yes/No
            display_df['Verified'] = display_df['Verified'].apply(lambda x: "✓ Yes" if x else "✗ No")
            
        if 'Verification Confidence' in display_df.columns:
            # Format confidence as percentage
            display_df['Verification Confidence'] = display_df['Verification Confidence'].apply(lambda x: f"{x*100:.0f}%")
        
        # Display the table
        st.dataframe(display_df, use_container_width=True)
        
        # Allow user to select an analysis to view in detail
        selected_analysis = st.selectbox("Select an analysis to view details:", 
                                        options=history_df['analysis_id'].tolist(),
                                        format_func=lambda x: f"{x.split('_')[0]} - {history_df[history_df['analysis_id']==x]['location'].values[0]}")
        
        if selected_analysis:
            # Get the analysis details
            metadata, satellite_image, flood_mask = get_analysis_details(selected_analysis)
            
            if metadata and satellite_image:
                st.markdown("### Analysis Details")
                
                # Display analysis information
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Location:** {metadata['location']}")
                    st.markdown(f"**Coordinates:** {metadata['latitude']:.5f}, {metadata['longitude']:.5f}")
                    st.markdown(f"**Satellite:** {metadata['satellite']}")
                    st.markdown(f"**Image Date:** {metadata['acquisition_date']}")
                
                with col2:
                    st.markdown(f"**Analysis Date:** {metadata['analysis_date']}")
                    st.markdown(f"**Flood Percentage:** {metadata['flood_percentage']:.2f}%")
                    st.markdown(f"**Model Used:** {metadata['model']}")
                    
                    # Show verification status if available
                    if 'verified' in metadata:
                        verified = metadata['verified']
                        if verified:
                            confidence = float(metadata.get('verification_confidence', 0.0))
                            st.markdown(f"**Verification:** ✓ Verified ({confidence*100:.0f}% confidence)")
                            
                            # Show verification sources if available
                            if 'verification_sources' in metadata and metadata['verification_sources']:
                                sources = metadata['verification_sources'].split(',')
                                sources_text = ", ".join(sources)
                                st.markdown(f"**Sources:** {sources_text}")
                        else:
                            st.markdown("**Verification:** ✗ Not verified by external sources")
                    
                    # Add a button to reload this analysis in the main Analysis tab
                    if st.button("Load in Analysis Tab"):
                        # Set session state variables to reload this analysis
                        st.session_state.load_from_history = True
                        st.session_state.history_metadata = metadata
                        st.session_state.history_satellite_image = satellite_image
                        st.session_state.history_flood_mask = flood_mask
                        st.session_state.current_tab = "Analysis"
                        st.rerun()
                
                # Display the images
                image_col1, image_col2 = st.columns(2)
                
                with image_col1:
                    st.image(satellite_image, caption="Satellite Image", use_container_width=True)
                
                with image_col2:
                    if flood_mask:
                        st.image(flood_mask, caption="Flood Detection Overlay", use_container_width=True)
                    else:
                        st.info("No flood mask image available for this analysis.")
                        
                # Generate and display a report
                flood_report = generate_flood_report(
                    metadata['location'], 
                    (metadata['latitude'], metadata['longitude']),
                    metadata['satellite'],
                    metadata['acquisition_date'],
                    metadata['flood_percentage']
                )
                
                st.markdown("### Analysis Report")
                st.markdown(flood_report)
                
                # Allow downloading the report
                st.download_button(
                    label="Download Report",
                    data=flood_report,
                    file_name=f"flood_analysis_{selected_analysis}.md",
                    mime="text/markdown",
                )
            else:
                st.error("Could not load the selected analysis details.")
                
elif st.session_state.current_tab == "Chat Assistant":
    # Chat assistant view
    st.markdown('<h2 class="section-header">Flood Analysis Assistant</h2>', unsafe_allow_html=True)
    
    if not st.session_state.results:
        st.markdown('<div class="info-box">Run a flood analysis first to enable the chat assistant with relevant context.</div>', unsafe_allow_html=True)
    else:
        # Display the chat interface
        display_chat()

else:  # Report tab
    # Report view
    st.markdown('<h2 class="section-header">Flood Analysis Report</h2>', unsafe_allow_html=True)
    
    if not st.session_state.report_text:
        st.markdown('<div class="info-box">Run a flood analysis first to generate a report.</div>', unsafe_allow_html=True)
    else:
        # Display the report
        st.markdown(st.session_state.report_text)
        
        # Allow downloading the report as text
        st.download_button(
            label="Download Report",
            data=st.session_state.report_text,
            file_name="flood_analysis_report.md",
            mime="text/markdown",
        )
