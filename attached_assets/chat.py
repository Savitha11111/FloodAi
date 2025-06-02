import os
import cohere
import streamlit as st
from datetime import datetime

# Initialize the Cohere client
API_KEY = os.getenv("COHERE_API_KEY", "")
co = cohere.Client(API_KEY) if API_KEY else None

def initialize_chat_history():
    """
    Initialize the chat history in the session state if it doesn't exist.
    """
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
        
    if 'chat_context' not in st.session_state:
        st.session_state.chat_context = {
            "location": None,
            "coordinates": None,
            "satellite_type": None,
            "acquisition_date": None,
            "flood_percentage": None,
            "flood_data": None
        }

def update_chat_context(location=None, coordinates=None, satellite_type=None, 
                        acquisition_date=None, flood_percentage=None, flood_data=None):
    """
    Update the chat context with the latest flood analysis data.
    
    Args:
        location: Location name
        coordinates: (lat, lon) tuple
        satellite_type: Type of satellite used for imagery
        acquisition_date: Date of satellite image acquisition
        flood_percentage: Percentage of area that is flooded
        flood_data: Additional data about the flood analysis
    """
    if 'chat_context' not in st.session_state:
        initialize_chat_history()
        
    if location:
        st.session_state.chat_context["location"] = location
    if coordinates:
        st.session_state.chat_context["coordinates"] = coordinates
    if satellite_type:
        st.session_state.chat_context["satellite_type"] = satellite_type
    if acquisition_date:
        st.session_state.chat_context["acquisition_date"] = acquisition_date
    if flood_percentage is not None:
        st.session_state.chat_context["flood_percentage"] = flood_percentage
    if flood_data:
        st.session_state.chat_context["flood_data"] = flood_data

def get_ai_response(user_message):
    """
    Get an AI-generated response using Cohere's chat API.
    
    Args:
        user_message: The user's message text
        
    Returns:
        str: The AI-generated response
    """
    if not co:
        return "Chat features are not available without a Cohere API key. Please provide your API key to enable conversational features."
    
    try:
        # Create context from flood data
        context = ""
        if st.session_state.chat_context["location"]:
            context += f"Location: {st.session_state.chat_context['location']}\n"
        
        if st.session_state.chat_context["coordinates"]:
            lat, lon = st.session_state.chat_context["coordinates"]
            context += f"Coordinates: Latitude {lat:.4f}, Longitude {lon:.4f}\n"
        
        if st.session_state.chat_context["satellite_type"]:
            context += f"Satellite: {st.session_state.chat_context['satellite_type']}\n"
            
        if st.session_state.chat_context["acquisition_date"]:
            context += f"Date: {st.session_state.chat_context['acquisition_date']}\n"
            
        if st.session_state.chat_context["flood_percentage"] is not None:
            context += f"Flood coverage: {st.session_state.chat_context['flood_percentage']:.1f}%\n"
        
        # Extract chat history for context (last 10 messages)
        chat_history = st.session_state.chat_history[-10:] if st.session_state.chat_history else []
        
        # Define system message with instructions
        system_message = f"""
        You are a helpful flood analysis assistant. The user is analyzing flood data using satellite imagery.
        
        Current analysis context:
        {context}
        
        Your role is to help interpret flood data, answer questions about flooding in the area, 
        provide insights about possible impacts, and suggest mitigation strategies.
        
        If asked about future predictions, you can provide general insights based on current data,
        but clarify that precise future predictions require more specialized modeling.
        
        Answer in a clear, concise manner. If you don't have specific information requested,
        suggest what data might be needed to provide a better answer.
        """
        
        # Format chat history for Cohere API
        formatted_history = []
        for msg in chat_history:
            role = "USER" if msg["is_user"] else "CHATBOT"
            formatted_history.append({
                "role": role,
                "message": msg["text"]
            })
            
        # Get response from Cohere
        response = co.chat(
            message=user_message,
            model="command",
            chat_history=formatted_history,
            preamble=system_message
        )
        
        return response.text
    except Exception as e:
        return f"I'm sorry, but I encountered an error processing your request. Error: {str(e)}"

def add_message(message, is_user=True):
    """
    Add a message to the chat history.
    
    Args:
        message: The message text
        is_user: Whether the message is from the user (True) or AI (False)
    """
    if 'chat_history' not in st.session_state:
        initialize_chat_history()
        
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.chat_history.append({
        "text": message,
        "is_user": is_user,
        "timestamp": timestamp
    })

def display_chat():
    """
    Display the chat interface and handle user interactions.
    """
    initialize_chat_history()
    
    # Display chat messages
    for message in st.session_state.chat_history:
        with st.chat_message("user" if message["is_user"] else "assistant"):
            st.write(message["text"])
    
    # Chat input
    if user_input := st.chat_input("Ask about flood data..."):
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        add_message(user_input, is_user=True)
        
        # Get and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_ai_response(user_input)
                st.write(response)
        
        add_message(response, is_user=False)

def generate_flood_report(location, coordinates, satellite_type, acquisition_date, 
                          flood_percentage, additional_data=None):
    """
    Generate a detailed report about the flood analysis.
    
    Args:
        location: Location name
        coordinates: (lat, lon) tuple
        satellite_type: Type of satellite used for imagery
        acquisition_date: Date of satellite image acquisition
        flood_percentage: Percentage of area that is flooded
        additional_data: Additional data about the flood analysis
        
    Returns:
        str: The flood report as a formatted text
    """
    lat, lon = coordinates
    
    report = f"""
    # Flood Analysis Report
    
    ## Location Information
    - **Location**: {location if location else "Not specified"}
    - **Coordinates**: Latitude {lat:.4f}, Longitude {lon:.4f}
    - **Analysis Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    ## Satellite Data
    - **Satellite**: {satellite_type}
    - **Image Acquisition Date**: {acquisition_date}
    
    ## Flood Analysis Results
    - **Flood Coverage**: {flood_percentage:.1f}% of the analyzed area
    - **Severity**: {get_severity_level(flood_percentage)}
    
    ## Interpretation
    {get_interpretation(flood_percentage)}
    
    ## Recommendations
    {get_recommendations(flood_percentage)}
    
    ---
    Report generated by Real-Time Flood Detection System
    """
    
    return report

def get_severity_level(flood_percentage):
    """Get the severity level based on flood percentage"""
    if flood_percentage < 5:
        return "Low"
    elif flood_percentage < 15:
        return "Moderate"
    elif flood_percentage < 30:
        return "High"
    else:
        return "Severe"

def get_interpretation(flood_percentage):
    """Get interpretation text based on flood percentage"""
    if flood_percentage < 5:
        return "The analysis indicates minimal flooding in the area. This level of water coverage is likely within normal ranges for the region."
    elif flood_percentage < 15:
        return "Moderate flooding detected. Some low-lying areas may be affected. Local waterways could be at elevated levels."
    elif flood_percentage < 30:
        return "Significant flooding detected. Many low-lying areas are likely inundated. Evacuation may be necessary for some residents in affected areas."
    else:
        return "Severe flooding detected. This represents a major flood event with potentially widespread impact. Immediate action may be required for safety."

def get_recommendations(flood_percentage):
    """Get recommendations based on flood percentage"""
    if flood_percentage < 5:
        return "- Continue monitoring if precipitation is expected\n- No immediate action required"
    elif flood_percentage < 15:
        return "- Monitor water levels in rivers and streams\n- Avoid low-lying areas\n- Be prepared for possible evacuation in flood-prone zones"
    elif flood_percentage < 30:
        return "- Evacuate from low-lying and flood-affected areas\n- Follow guidance from local emergency services\n- Prepare for possible infrastructure disruptions"
    else:
        return "- Immediately evacuate from all flood-affected areas\n- Seek higher ground\n- Follow emergency protocols and official guidance\n- Prepare for significant infrastructure disruptions"
