import streamlit as st

# Routes
# Page Setup
about_page = st.Page(
	  page = "views/about.py",
	  title = "About",
	  icon=":material/home:",
	  default=True
	)

interview_page = st.Page(
	  page = "views/interview.py",
	  title = "AI Interviewer",
	  icon=":material/smart_toy:"
	)

# Navigation Setup
pg = st.navigation(pages=[about_page, interview_page])

# Run the Navigation
pg.run()