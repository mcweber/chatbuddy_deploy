# ---------------------------------------------------
# Version: 22.07.2024
# Author: M. Weber
# ---------------------------------------------------
# 
# ---------------------------------------------------

import streamlit as st
import chatbuddy_module as module
import chatbuddy_user as user

SEARCH_TYPES = ("llm", "rag")

# Functions -------------------------------------------------------------

@st.experimental_dialog("Login User")
def login_user_dialog() -> None:
    with st.form(key="loginForm"):
        st.write(f"Status: {st.session_state.userStatus}")
        user_name = st.text_input("Benutzer")
        user_pw = st.text_input("Passwort", type="password")
        if st.form_submit_button("Login"):
            if user_name and user_pw:
                active_user = chatbuddy_user.check_user(user_name, user_pw)
                if active_user:
                    st.session_state.userName = active_user["username"]
                    st.session_state.userRole = active_user["rolle"]
                    st.session_state.userStatus = 'True'
                    st.rerun()
                else:
                    st.error("User not found.")
            else:
                st.error("Please fill in all fields.")

def write_history() -> None:
    for entry in st.session_state.history:
        if entry["role"] == "user":
            with st.chat_message("user"):
                st.write(f"User: {entry['content']}")
        elif entry["role"] == "assistant":
            with st.chat_message("assistant"):
                st.write(f"Assistant: {entry['content']}")

# Main -----------------------------------------------------------------
def main() -> None:
    st.set_page_config(page_title='chatbuddy', initial_sidebar_state="collapsed")
    
    # Initialize Session State -----------------------------------------
    if 'init' not in st.session_state:
        # Check if System-Prompt exists
        if user.get_systemprompt() == {}:
            temp_id = user.add_systemprompt("Du bist ein hilfreicher Assistent.")
            st.warning(f"System-Prompt wurde erstellt: {temp_id}")
        st.session_state.init: bool = True
        st.session_state.history: list = []
        st.session_state.llmStatus: str = module.LLMS[0]
        st.session_state.marktbereich: str = "Alle"
        st.session_state.marktbereichIndex: int = 0
        st.session_state.results: str = ""
        # st.session_state.searchPref: str = "Artikel"
        st.session_state.searchResultsLimit:int  = 50
        st.session_state.searchStatus: bool = False
        st.session_state.searchType: str = "llm"
        st.session_state.searchTypeIndex: int  = SEARCH_TYPES.index(st.session_state.searchType)
        st.session_state.showLatest: bool = False
        st.session_state.systemPrompt: str = user.get_systemprompt()
        st.session_state.userName: str = ""
        st.session_state.userRole: str = ""
        st.session_state.userStatus: bool = True
        st.session_state.webSearch: str = "tavily" # tavily, DDGS
   
    # if st.session_state.userStatus == False:
    #     login_user_dialog()
    
    # Define Sidebar ---------------------------------------------------
    with st.sidebar:
        st.header("ChatBuddy")
        st.caption("Version: 22.07.2024 Status: POC")
        if st.session_state.userStatus:
            st.caption(f"Eingeloggt als: {st.session_state.userName}")
        else:
            st.caption("Nicht eingeloggt.")
        switch_searchType = st.radio(label="Auswahl Suchtyp", options=SEARCH_TYPES, index=st.session_state.searchTypeIndex, horizontal=True)
        if switch_searchType != st.session_state.searchType:
            st.session_state.searchType = switch_searchType
            st.session_state.searchTypeIndex = SEARCH_TYPES.index(switch_searchType)
            st.rerun()
        switch_search_results = st.slider("Search Results", 1, 100, st.session_state.searchResultsLimit)
        if switch_search_results != st.session_state.searchResultsLimit:
            st.session_state.searchResultsLimit = switch_search_results
            st.rerun()
        switch_llm = st.radio(label="Switch LLM", options=module.LLMS, index=0)
        if switch_llm != st.session_state.llmStatus:
            st.session_state.llmStatus = switch_llm
            st.rerun()
        switch_webSearch = st.radio(label="Switch Web-Suche", options=("tavily", "DDGS"), index=0)
        if switch_webSearch != st.session_state.webSearch:
            st.session_state.webSearch = switch_webSearch
            st.rerun()
        st.divider()
        switch_SystemPrompt = st.text_area("System-Prompt", st.session_state.systemPrompt, height=200)
        if switch_SystemPrompt != st.session_state.systemPrompt:
            st.session_state.systemPrompt = switch_SystemPrompt
            user.update_systemprompt(switch_SystemPrompt)
            st.rerun()
        st.divider()
        st.text_area("History", st.session_state.history, height=200)
        if st.button("Clear History"):
            st.session_state.history = [{"role": "system", "content": user.get_systemprompt()}]
            st.rerun()
        
    # Define Search Form ----------------------------------------------
    prompt = st.chat_input("Frage eingeben:")
    if prompt:
        st.session_state.searchStatus = True

    # Define Search & Search Results -------------------------------------------
    web_results_str = ""
    if st.session_state.userStatus and st.session_state.searchStatus:
        if st.session_state.searchType == "rag":
            # Web Search ------------------------------------------------
            if st.session_state.webSearch == "tavily":
                results = module.web_search_tavily(query=prompt, score=0.5, limit=10)
                with st.expander("WEB Suchergebnisse"):
                    for result in results:
                        st.write(f"[{round(result['score'], 3)}] {result['title']} [{result['url']}]")
                        web_results_str += f"Titel: {result['title']}\nURL: {result['url']}\nText: {result['raw_content']}\n\n"
            else:
                results = module.web_search_ddgs(query=prompt, limit=10)
                with st.expander("WEB Suchergebnisse"):
                    for result in results:
                        st.write(f"{result['title']} [{result['href']}]")
                        web_results_str += f"Titel: {result['title']}\nURL: {result['href']}\nText: {result['body']}\n\n"
        with st.expander("web_results_str"):
                st.write(web_results_str)
        # LLM Search ------------------------------------------------
        summary = module.ask_llm(
            llm=st.session_state.llmStatus,
            temperature=0.2,
            question=prompt,
            history=st.session_state.history,
            systemPrompt=st.session_state.systemPrompt,
            # db_results_str="",
            web_results_str=web_results_str
            )
        # with st.chat_message("assistant"):
        #     # st.write(prompt)
        #     st.write(summary)
        st.session_state.history.append({"role": "user", "content": prompt})
        st.session_state.history.append({"role": "assistant", "content": summary})
        write_history()
        st.session_state.searchStatus = False

if __name__ == "__main__":
    main()
