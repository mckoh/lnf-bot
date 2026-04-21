import streamlit as st
import os
import random
import gspread
from google.oauth2.service_account import Credentials
from pandas import DataFrame


HUMAN_DIR = "img/real"
KI_DIR = "img/ki"
NUM_IMAGES = 5
HUMAN_TEXT = "### Echte Aufnahme"
KI_TEST = "### KI Bild"

with open("explanations.txt", "r", encoding="utf-8") as file:
    explanations = file.readlines()


def main():
    st.set_page_config(
        page_title="LNF 2026: Mensch vs. KI",
        page_icon="🤖",
        layout="wide"
    )

    st.title("Was ist echt, was ist fake?")
    st.markdown("Erkennst du den Unterschied? Wähle das Bild aus, das deiner Meinung nach von einer **KI** generiert wurde. Klicke dazu auf den Button unterhalb des jeweiligen Bildes.")

    # 1. Überprüfung der Ordnerstruktur
    if not os.path.exists(HUMAN_DIR) or not os.path.exists(KI_DIR):
        st.error(f"Ordner nicht gefunden! Bitte erstelle die Verzeichnisse '{HUMAN_DIR}' und '{KI_DIR}' im Projektordner.")
        return

    # 2. Quiz-Daten initialisieren (nur beim ersten Start)
    if 'quiz_data' not in st.session_state:
        human_files = sorted([f for f in os.listdir(HUMAN_DIR) if f.lower().endswith(('.png'))])
        ki_files = sorted([f for f in os.listdir(KI_DIR) if f.lower().endswith(('.png'))])

        # Wir bilden Paare basierend auf der kleinsten gemeinsamen Anzahl an Bildern
        if len(human_files) != len(ki_files):
            st.warning("Ungleich viele Bilder im ki- und real-Ordner")
            return

        num_pairs = len(human_files)

        if num_pairs == 0:
            st.warning("Keine Bilder in den Ordnern gefunden. Bitte lade Bilder hoch.")
            return

        asked = []
        pairs = []
        for i in range(num_pairs):
            # Zufällig entscheiden, ob das KI-Bild links oder rechts erscheint
            ki_on_left = random.choice([True, False])
            pairs.append({
                "index": i,
                "human": os.path.join(HUMAN_DIR, human_files[i]),
                "ki": os.path.join(KI_DIR, ki_files[i]),
                "ki_on_left": ki_on_left
            })

        random.shuffle(pairs)
        st.session_state.quiz_data = pairs[:NUM_IMAGES]
        st.session_state.current_idx = 0
        st.session_state.score = 0
        st.session_state.finished = False
        st.session_state.quiz_results = []

    # 3. Anzeige der Auswertung am Ende
    if st.session_state.finished:

        st.balloons()
        st.markdown(f"## Quiz beendet mit **{st.session_state.score} von {len(st.session_state.quiz_data)}** richtig erkannten Bilder")

        if st.button("Quiz neu starten"):
            del st.session_state.quiz_data
            del st.session_state.quiz_results
            st.rerun()

        incorrect_answers = [res for res in st.session_state.quiz_results if not res['is_correct']]
        asked_indexes = [img["index"] for img in st.session_state.quiz_data]
        incorrect_indexes = [img["index"] for img in incorrect_answers]

        st.write(",".join(asked_indexes))
        st.write(",".join(incorrect_indexes))

        store_results(
            ",".join(asked_indexes),
            ",".join(incorrect_indexes),
            str(len(incorrect_indexes)/len(asked_indexes))
        )

        if incorrect_answers:

            st.markdown("## Bilder bei denen du falsch lagst")
            for i, result in enumerate(incorrect_answers):

                col_err1, col_err2 = st.columns(2)

                with col_err1:
                    st.markdown(HUMAN_TEXT)
                    st.image(result['human_img'])

                with col_err2:
                    st.markdown(KI_TEST)
                    st.image(result['ki_img'])

                st.markdown("Du hattest das reale Bild für das KI-Bild gehalten. **Woran du hier das KI-Bild erkennen hättest können:** " + explanations[result["index"]])

                st.markdown("---")

        return

    # 4. Quiz-Loop
    idx = st.session_state.current_idx
    pair = st.session_state.quiz_data[idx]

    # Bestimmen, welches Bild in welcher Spalte ist
    left_img, right_img = (pair['ki'], pair['human']) if pair['ki_on_left'] else (pair['human'], pair['ki'])
    left_is_ki = pair['ki_on_left']

    st.progress(idx / len(st.session_state.quiz_data))
    st.subheader(f"Bildpaar {idx + 1} von {len(st.session_state.quiz_data)}")

    col1, col2 = st.columns(2)

    # Bestimmen, welches Bild in welche Spalte kommt
    with col1:
        st.image(left_img, use_container_width=True)
        if st.button("Das linke Bild ist KI 👈", key=f"btn_l_{idx}"): # User wählt links als KI
            check_answer(user_chose_left_as_ki=True, correct_ki_is_on_left=left_is_ki)

    with col2:
        st.image(right_img, use_container_width=True)
        if st.button("Das rechte Bild ist KI 👉", key=f"btn_r_{idx}"): # User wählt rechts als KI
            check_answer(user_chose_left_as_ki=False, correct_ki_is_on_left=left_is_ki)

def check_answer(user_chose_left_as_ki, correct_ki_is_on_left):
    current_pair = st.session_state.quiz_data[st.session_state.current_idx]
    is_correct = (user_chose_left_as_ki == correct_ki_is_on_left)

    if is_correct:
        st.session_state.score += 1

    # Speichern der Ergebnisse für die Auswertung am Ende
    st.session_state.quiz_results.append({
        "question_number": st.session_state.current_idx + 1,
        "human_img": current_pair['human'],
        "ki_img": current_pair['ki'],
        "ki_on_left_for_display": current_pair['ki_on_left'], # Wie es dem Benutzer angezeigt wurde
        "user_chose_left_as_ki": user_chose_left_as_ki, # Was der Benutzer gewählt hat
        "is_correct": is_correct,
        "index": current_pair["index"]
    })

    if st.session_state.current_idx + 1 < len(st.session_state.quiz_data):
        st.session_state.current_idx += 1
    else:
        st.session_state.finished = True
    st.rerun()

def store_results(img_received, img_correct, score):
    creds = Credentials.from_service_account_info(

    st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )

    client = gspread.authorize(creds)

    workbook = client.open_by_key(st.secrets["google_sheet"]["sheet_id"])
    worksheet = workbook.worksheet("Sheet1")

    # read all data from worksheet
    data = DataFrame(worksheet.get_all_values())
    data.columns = data.iloc[0]
    data.drop(0, axis=0, inplace=True)



if __name__ == "__main__":
    main()
