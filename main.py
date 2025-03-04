import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import folium.plugins
from geopy.geocoders import Nominatim
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import pytz
import uuid

# Load credentials from Streamlit secrets
firebase_credentials = st.secrets["firebase"]

# Check if Firebase app is already initialized
if not firebase_admin._apps:
    # Create a credential object
    cred = credentials.Certificate({
    "type": firebase_credentials["type"],
    "project_id": firebase_credentials["project_id"],
    "private_key_id": firebase_credentials["private_key_id"],
    "private_key": firebase_credentials["private_key"].replace("\\n", "\n"),  # Fix newline escape sequence
    "client_email": firebase_credentials["client_email"],
    "client_id": firebase_credentials["client_id"],
    "auth_uri": firebase_credentials["auth_uri"],
    "token_uri": firebase_credentials["token_uri"],
    "auth_provider_x509_cert_url": firebase_credentials["auth_provider_x509_cert_url"],
    "client_x509_cert_url": firebase_credentials["client_x509_cert_url"]
    })
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Function to save data to Firebase Firestore
def save_to_firebase(collection, data):
    try:
        doc_ref = db.collection(collection).document()
        doc_ref.set(data)
        return doc_ref.id
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return None

# Function to remove data from Firebase Firestore
def remove_from_firebase(collection, document_id):
    try:
        db.collection(collection).document(document_id).delete()
        st.success(f"Document {document_id} deleted successfully.")
    except Exception as e:
        st.error(f"Error deleting document: {e}")

# Function to retrieve data from Firebase Firestore
def get_from_firebase(collection):
    try:
        docs = db.collection(collection).stream()
        return {doc.id: doc.to_dict() for doc in docs}
    except Exception as e:
        st.error(f"Error retrieving data: {e}")
        return {}

# Sample itinerary data
data = {
    "Date": ["11 August", "12 August", "13-18 August", "18-19 August", "19-21 August", "24-25 August"],
    "Location": ["Flight to South Korea", "Arrival in South Korea", "Seoul", "Gyeongju", "Busan", "Return to Denmark"],
    "Activities": [
        "Boarding and flight details",
        "Arrival and check-in",
        "Explore Seoul: Gyeongbokgung Palace, N Seoul Tower, etc.",
        "Visit historic sites: Bulguksa Temple, Cheomseongdae Observatory",
        "Explore Busan: Haeundae Beach, Jagalchi Fish Market",
        "Flight back home"
    ]
}

# Initialize session state for editable data if it doesn't exist
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = pd.DataFrame(data)

# Set page configuration
st.set_page_config(page_title="Travel Itinerary", layout="wide", initial_sidebar_state="expanded")

# Sidebar overview with dropdown menu
sidebar_menu = st.sidebar.selectbox(
    "📅 Overview",
    ["Home", "Itinerary", "Flights", "Notes", "Hotels", "Must Try Eat", "What to Pack"]
)

# Set custom font and style
st.markdown("""<style>
    .css-ffhzg2 { font-family: 'Verdana', sans-serif; font-size: 16px; }
    .css-1d391kg { font-family: 'Verdana', sans-serif; }
    .stButton button { background-color: #4CAF50; color: white; font-size: 16px; }
    body { background-color: #f0f4f8; }
    .stTextInput>div>input { background-color: #e0f7fa; }
    .stTextArea>div>textarea { background-color: #e0f7fa; }
    .css-1d391kg { color: #00796b; }
</style>""", unsafe_allow_html=True)

# Display map with search feature
if sidebar_menu == "Home":
    st.title("🌍 Welcome to Our South Korea Travel Itinerary!")
    st.write("Here, you can manage your travel plans, locations, and activities. Navigate through the sidebar to edit your itinerary, add notes, and more.")
    st.write("Dette er lavet for sjovs skyld, håber selvfølgelig vi kommer til at bruge det :D")
    st.image("southKoreaHero.jpg", caption="Wohoo!", width=500)

elif sidebar_menu == "Itinerary":
    st.title("🌍 Travel Itinerary - South Korea")

    st.write("### 📅 Trip Overview")
    st.dataframe(st.session_state.itinerary, use_container_width=True)

    st.write("### 📅 Your Itinerary")
    for i, row in st.session_state.itinerary.iterrows():
        with st.expander(f"📅 {row['Date']} - {row['Location']}"):
            st.markdown(f"#### 📍 Location: {row['Location']}")
            st.markdown(f"#### 🎯 Activities: {row['Activities']}")

            edited_location = st.text_input(f"Edit location for {row['Date']}", row['Location'], key=f"edit_loc_{i}")
            edited_activities = st.text_area(f"Edit activities for {row['Date']}", row['Activities'], key=f"edit_activities_{i}")
            
            if st.button(f"Save changes for {row['Date']}", key=f"save_button_{i}"):
                st.session_state.itinerary.at[i, 'Location'] = edited_location
                st.session_state.itinerary.at[i, 'Activities'] = edited_activities
                save_to_firebase("itinerary", {"Date": row['Date'], "Location": edited_location, "Activities": edited_activities})
                st.success(f"Updated entry for {row['Date']}!")

    with st.expander("➕ Add New Entry"):
        new_date = st.text_input("New Date")
        new_location = st.text_input("New Location")
        new_activities = st.text_area("New Activities")
        
        if st.button("Add New Entry"):
            if new_date and new_location and new_activities:
                new_entry = pd.DataFrame({"Date": [new_date], "Location": [new_location], "Activities": [new_activities]})
                st.session_state.itinerary = pd.concat([st.session_state.itinerary, new_entry], ignore_index=True)
                save_to_firebase("itinerary", {"Date": new_date, "Location": new_location, "Activities": new_activities})
                st.success(f"Added new entry for {new_date}")
            else:
                st.error("Please fill out all fields to add a new entry.")

elif sidebar_menu == "Flights":
    st.title("✈️ Flights - Detailed Flight Information")

    # Outbound Flight: Copenhagen to Seoul (Monday, 11 August 2025)
    st.write("### ✈️ Outbound Flight: Copenhagen to Seoul (Monday, 11 August 2025)")

    # Display outbound flight details
    st.write(f"**Departure**: Monday, 11 August 2025 at 16:00 from (CPH)")
    st.write(f"**Arrival**: Monday, 11 August 2025 at 23:00 in (DOH)")
    st.write(f"**Flight Number**: QR 160 by Qatar Airways")
    st.write(f"**Baggage Allowance**: 25 kg (Adult, Economy Class)")
    st.write(f"**Connection Time**: 3 hours 20 minutes")
    st.write(f"**Transit Time**: 6 hours 0 minutes")
    st.write(f"**Connection Flight**: Tuesday, 12 August 2025 at 02:20 from (DOH) to Seoul Qatar Airways")
    st.write(f"**Arrival at Destination**: Tuesday, 12 August 2025 at 17:05 at (ICN) Seoul ")

    st.write("---")

    # Inbound Flight: Seoul to Copenhagen (Monday, 25 August 2025)
    st.write("### ✈️ Inbound Flight: Seoul to Copenhagen (Monday, 25 August 2025)")

    # Display inbound flight details
    st.write(f"**Departure**: Monday, 25 August 2025 at 01:20 from (ICN) South Korea")
    st.write(f"**Arrival**: Monday, 25 August 2025 at 05:30 in (DOH), Qatar")
    st.write(f"**Flight Number**: QR 859 by Qatar Airways)")
    st.write(f"**Baggage Allowance**: 25 kg (Adult, Economy Class)")
    st.write(f"**Connection Time**: 3 hours 10 minutes")
    st.write(f"**Transit Time**: 6 hours 25 minutes")
    st.write(f"**Connection Flight**: Monday, 25 August 2025 at 08:40 from Doha to Copenhagen by Qatar Airways)")
    st.write(f"**Arrival at Destination**: Monday, 25 August 2025 at 14:05 at(CPH), Denmark")


elif sidebar_menu == "Notes":
    st.title("📝 Notes - Add and Edit Notes")

    # Retrieve notes from Firebase
    notes = get_from_firebase("notes")

    if isinstance(notes, dict) and notes:  # Ensure it's a dictionary and not empty
        st.write("### 📝 Your Notes")

        for note_id, note in notes.items():
            section = note.get("section", "Untitled")
            subsection = note.get("subsection", "No content")

            with st.expander(f"📌 {section}"):
                st.markdown(f"**Subsection:** {subsection}")

                # Edit section and subsection
                edited_section = st.text_input("Edit Section", value=section, key=f"edit_section_{note_id}")
                edited_subsection = st.text_area("Edit Subsection", value=subsection, key=f"edit_subsection_{note_id}")

                # Save changes button
                if st.button("💾 Save Changes", key=f"save_{note_id}"):
                    if edited_section and edited_subsection:
                        updated_note = {"section": edited_section, "subsection": edited_subsection}
                        # Update the note in Firestore using the correct document ID
                        db.collection("notes").document(note_id).set(updated_note)
                        st.success(f"Updated note: {edited_section}")
                    else:
                        st.error("Both fields must be filled!")

                # Delete button
                if st.button("❌ Delete Note", key=f"delete_{note_id}"):
                    remove_from_firebase("notes", note_id)  # Remove note
                    st.success(f"Note '{section}' deleted!")

    else:
        st.warning("No notes found. Start by adding one below.")

    # Add a new note form
    st.write("### ➕ Add a New Note")
    new_section = st.text_input("Section", key="new_section")
    new_subsection = st.text_area("Subsection", key="new_subsection")

    if st.button("➕ Save New Note"):
        if new_section and new_subsection:
            # Create a new note document in Firestore
            note_data = {"section": new_section, "subsection": new_subsection}
            doc_ref = db.collection("notes").document()  # Auto-generate a document ID
            doc_ref.set(note_data)  # Save the new note
            st.success(f"New note '{new_section}' added!")
        else:
            st.error("Please fill out both fields before saving.")

elif sidebar_menu == "Hotels":
    st.title("🏨 Hotels - Where You Sleep")

    # Add a new hotel form
    st.write("### 🏨 Add a New Hotel")
    name = st.text_input("Hotel Name")
    location = st.text_input("Hotel Location")
    check_in_time = st.text_input("Check-in Time (e.g., 2025-03-15 03:00 PM)")
    check_out_time = st.text_input("Check-out Time (e.g., 2025-03-17 11:00 AM)")

    try:
        check_in_time = datetime.strptime(check_in_time, "%Y-%m-%d %I:%M %p") if check_in_time else None
        check_out_time = datetime.strptime(check_out_time, "%Y-%m-%d %I:%M %p") if check_out_time else None
    except ValueError:
        check_in_time = None
        check_out_time = None
        st.error("Invalid time format. Please use 'YYYY-MM-DD HH:MM AM/PM' format.")

    if st.button("Save Hotel"):
        if name and location and check_in_time and check_out_time:
            hotel_data = {
                "name": name,
                "location": location,
                "check_in_time": check_in_time,
                "check_out_time": check_out_time
            }
            save_to_firebase("hotels", hotel_data)
            st.success(f"Hotel {name} added successfully!")

    # Display existing hotel details from Firebase and allow editing
    hotels = get_from_firebase("hotels")
    if hotels:
        st.write("### 🏨 Your Hotels")
        for hotel_id, hotel in hotels.items():
            # Use the hotel name in the expander and other UI elements
            with st.expander(f"Edit {hotel['name']}"):
                edited_name = st.text_input(f"Edit Hotel Name", value=hotel['name'], key=f"edit_name_{hotel_id}")
                edited_location = st.text_input(f"Edit Location", value=hotel['location'], key=f"edit_location_{hotel_id}")
                edited_check_in_time = st.text_input(f"Edit Check-in Time", value=hotel['check_in_time'].strftime('%Y-%m-%d %I:%M %p'), key=f"edit_check_in_time_{hotel_id}")
                edited_check_out_time = st.text_input(f"Edit Check-out Time", value=hotel['check_out_time'].strftime('%Y-%m-%d %I:%M %p'), key=f"edit_check_out_time_{hotel_id}")

                if st.button(f"Save Changes for {hotel['name']}", key=f"save_hotel_{hotel_id}"):
                    updated_hotel = {
                        "name": edited_name,
                        "location": edited_location,
                        "check_in_time": datetime.strptime(edited_check_in_time, "%Y-%m-%d %I:%M %p"),
                        "check_out_time": datetime.strptime(edited_check_out_time, "%Y-%m-%d %I:%M %p")
                    }
                    # Update the hotel document in Firebase using the hotel_id
                    db.collection("hotels").document(hotel_id).set(updated_hotel)
                    st.success(f"Hotel {hotel['name']} updated successfully!")

            # Add a button to remove the hotel
            if st.button(f"❌ Remove {hotel['name']}", key=f"remove_hotel_{hotel_id}"):
                remove_from_firebase("hotels", hotel_id)
                st.success(f"Hotel {hotel['name']} removed successfully!")

elif sidebar_menu == "Must Try Eat":
    st.title("🍽 Must Try Eat")

    # Retrieve must-try foods from Firebase
    must_try_foods = get_from_firebase("must_try_foods")

    # Display existing must-try foods with checkboxes and allow editing
    st.write("### 🥢 Must Try Foods List")

    if must_try_foods:
        for food_id, food_data in must_try_foods.items():
            food = food_data["food"]
            location = food_data["where_to_get"]

            col1, col2 = st.columns([8, 2])  # More space for the food name, less for the buttons
            with col1:
                with st.expander(f"Edit details for: {food}"):
                    # Edit form for each food item
                    edited_food = st.text_input(f"Edit Food Name", value=food, key=f"edit_food_{food_id}")
                    edited_location = st.text_input(f"Edit Location", value=location, key=f"edit_location_{food_id}")

                    if st.button(f"Save Changes for {food}", key=f"save_food_{food_id}"):
                        if edited_food and edited_location:
                            updated_food = {
                                "food": edited_food,
                                "where_to_get": edited_location
                            }
                            save_to_firebase("must_try_foods", updated_food)
                            st.success(f"Updated {food}!")
                        else:
                            st.error("Please make sure both food name and location are filled.")

            with col2:
                # Remove button for each food item
                if st.button(f"❌ Remove {food}", key=f"remove_food_{food_id}"):
                    remove_from_firebase("must_try_foods", food_id)
                    st.success(f"Removed {food} successfully!")

    # Option to add a new food item
    st.write("### 🥢 Add a New Must Try Food")
    new_food = st.text_input("Food Name")
    new_location = st.text_input("Where to Get It")

    if st.button("Add New Food"):
        if new_food and new_location:
            save_to_firebase("must_try_foods", {"food": new_food, "where_to_get": new_location})
            st.success(f"Added {new_food} to your must-try list!")
        else:
            st.error("Please make sure both fields are filled before adding.")
