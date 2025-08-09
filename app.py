import streamlit as st
import pywhatkit as kit
import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# --- Backend Functions ---

def send_pywhatkit_message(phone_no: str, message: str, schedule_time: dict):
    """Sends a WhatsApp message using pywhatkit automation."""
    if schedule_time['instant']:
        kit.sendwhatmsg_instantly(
            phone_no=phone_no,
            message=message,
            wait_time=15,
            tab_close=True
        )
    else:
        now = datetime.datetime.now()
        # FIXED: Robust time calculation using timedelta
        send_time = now + datetime.timedelta(minutes=schedule_time['delay'])
        kit.sendwhatmsg(
            phone_no=phone_no,
            message=message,
            time_hour=send_time.hour,
            time_min=send_time.minute
        )

def send_twilio_message(sid: str, token: str, from_num: str, to_num: str, message: str):
    """Sends a WhatsApp message using the Twilio API."""
    try:
        client = Client(sid, token)
        # FIXED: Correctly prefixes the recipient number with "whatsapp:"
        formatted_to_num = f"whatsapp:{to_num}"
        
        msg = client.messages.create(
            body=message,
            from_=from_num,
            to=formatted_to_num
        )
        return True, f"Message sent successfully! SID: {msg.sid}"
    except TwilioRestException as e:
        return False, f"Twilio Error: {e.msg}"
    except Exception as e:
        return False, f"An unexpected error occurred: {str(e)}"

# --- Streamlit App ---


  st.set_page_config(page_title="WhatsApp Sender", layout="centered", page_icon="📱")
  st.title("📱 WhatsApp Message Sender")
  
  tab1, tab2 = st.tabs(["WhatsApp Web Automation", "Twilio API"])

  # --- Tab 1: WhatsApp Web Automation via pywhatkit ---
  with tab1:
      st.header("Send via WhatsApp Web")
      st.markdown("This method automates WhatsApp Web in your local browser.")
      st.warning(
          "⚠️ **This only works when running Streamlit on your own desktop computer.** It will not work if deployed to a server."
      )
      st.info("Make sure you are logged into WhatsApp Web in your default browser before sending.")

      with st.form("whatsapp_web_form"):
          phone_number = st.text_input("📞 Phone Number (with country code)", "+91")
          message = st.text_area("💬 Your Message", height=100)
          
          # FIXED: Clearer UI for scheduling options
          send_option = st.radio(
              "When to send?",
              ("Send Instantly", "Schedule for Later"),
              horizontal=True
          )
          
          delay_minutes = 0
          if send_option == "Schedule for Later":
              delay_minutes = st.number_input("Delay (minutes from now)", min_value=1, max_value=60, value=5)
          
          submit_button = st.form_submit_button("🚀 Send Message via Browser", use_container_width=True)

      if submit_button:
          if phone_number and message:
              schedule = {'instant': send_option == "Send Instantly", 'delay': delay_minutes}
              with st.spinner("Preparing to send message..."):
                  try:
                      send_pywhatkit_message(phone_number, message, schedule)
                      st.success("✅ WhatsApp Web has been opened to send your message!")
                      st.balloons()
                  except Exception as e:
                      st.error(f"❌ Error: {str(e)}")
          else:
              st.warning("⚠️ Please fill in both phone number and message.")

  # --- Tab 2: Twilio API ---
  with tab2:
      st.header("Send via Twilio API")
      st.markdown("This method sends messages directly using the Twilio API (no browser needed). It is reliable and works on deployed servers.")
      
      # FIXED: Loads credentials securely from st.secrets
      try:
          default_sid = st.secrets.get("TWILIO_ACCOUNT_SID", "")
          default_token = st.secrets.get("TWILIO_AUTH_TOKEN", "")
          default_from_num = st.secrets.get("TWILIO_WHATSAPP_NUMBER", "")
      except FileNotFoundError:
          default_sid = default_token = default_from_num = ""
          st.info("Create a `.streamlit/secrets.toml` file to pre-fill your credentials.")
          
      with st.form("twilio_form"):
          account_sid = st.text_input("Twilio Account SID", value=default_sid, type="password")
          auth_token = st.text_input("Twilio Auth Token", value=default_token, type="password")
          from_number = st.text_input("Your Twilio WhatsApp Number", value=default_from_num)
          to_number = st.text_input("📞 Recipient's Number (with country code)", "+91")
          api_message = st.text_area("💬 Message", key="twilio_message")
          
          submit_api_button = st.form_submit_button("📲 Send Message via API", use_container_width=True)

      if submit_api_button:
          if all([account_sid, auth_token, from_number, to_number, api_message]):
              with st.spinner("Sending message via Twilio..."):
                  success, response_message = send_twilio_message(
                      account_sid, auth_token, from_number, to_number, api_message
                  )
                  if success:
                      st.success(f"✅ {response_message}")
                  else:
                      st.error(f"❌ {response_message}")
          else:
              st.warning("⚠️ Please fill in all required fields.")

if __name__ == "__main__":
  run_app()
