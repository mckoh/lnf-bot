import streamlit as st
import os
import random


HUMAN_DIR = "img/real"
KI_DIR = "img/ki"
NUM_IMAGES = 5

def main():
    st.set_page_config(
        page_title="LNF 2026: Mensch vs. KI",
        page_icon="🤖",
        layout="wide"
    )

    st.title("🤖 Mensch oder Maschine?")
    st.write("Erkennst du den Unterschied? Wähle das Bild aus, das deiner Meinung nach von einer **KI** generiert wurde.")

    # 1. Überprüfung der Ordnerstruktur
    if not os.path.exists(HUMAN_DIR) or not os.path.exists(KI_DIR):
        st.error(f"Ordner nicht gefunden! Bitte erstelle die Verzeichnisse '{HUMAN_DIR}' und '{KI_DIR}' im Projektordner.")
        return

    # 2. Quiz-Daten initialisieren (nur beim ersten Start)
    if 'quiz_data' not in st.session_state:
        human_files = sorted([f for f in os.listdir(HUMAN_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])
        ki_files = sorted([f for f in os.listdir(KI_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))])

        # Wir bilden Paare basierend auf der kleinsten gemeinsamen Anzahl an Bildern
        num_pairs = min(len(human_files), len(ki_files))

        if num_pairs == 0:
            st.warning("Keine Bilder in den Ordnern gefunden. Bitte lade Bilder hoch.")
            return

        pairs = []
        for i in range(num_pairs):
            # Zufällig entscheiden, ob das KI-Bild links oder rechts erscheint
            ki_on_left = random.choice([True, False])
            pairs.append({
                "human": os.path.join(HUMAN_DIR, human_files[i]),
                "ki": os.path.join(KI_DIR, ki_files[i]),
                "ki_on_left": ki_on_left
            })

        random.shuffle(pairs)
        st.session_state.quiz_data = pairs[:NUM_IMAGES]
        st.session_state.current_idx = 0
        st.session_state.score = 0
        st.session_state.finished = False
        st.session_state.quiz_results = [] # Speichert die Ergebnisse jeder Frage

    # 3. Anzeige der Auswertung am Ende
    if st.session_state.finished:
        st.balloons()
        st.header("Quiz beendet!")

        st.metric("Dein Score", f"{st.session_state.score} von {len(st.session_state.quiz_data)} richtig erkannt")

        if st.button("Quiz neu starten"):
            del st.session_state.quiz_data
            del st.session_state.quiz_results
            st.rerun()

        incorrect_answers = [res for res in st.session_state.quiz_results if not res['is_correct']]

        if incorrect_answers:
            st.subheader("Diese Bilder hast du diesmal nicht richtig erkannt:")
            for i, result in enumerate(incorrect_answers):
                st.markdown(f"--- **Frage {result['question_number']}** ---")

                col_err1, col_err2 = st.columns(2)

                # Bestimmen, welches Bild tatsächlich KI war und welches Mensch
                actual_ki_img = result['ki_img']
                actual_human_img = result['human_img']

                # Bestimmen, wie die Bilder angezeigt wurden
                if result['ki_on_left_for_display']:
                    displayed_left_img = actual_ki_img
                    displayed_right_img = actual_human_img
                else:
                    displayed_left_img = actual_human_img
                    displayed_right_img = actual_ki_img

                with col_err1:
                    st.image(displayed_left_img, width=300)
                    if displayed_left_img == actual_ki_img:
                        st.markdown("**Dieses Bild war von einer KI.**")
                    else:
                        st.markdown("Dieses Bild war von einem Menschen.")

                with col_err2:
                    st.image(displayed_right_img, width=300)
                    if displayed_right_img == actual_ki_img:
                        st.markdown("**Dieses Bild war von einer KI.**")
                    else:
                        st.markdown("Dieses Bild war von einem Menschen.")

                if result['user_chose_left_as_ki']:
                    st.markdown("Du hast das **linke** Bild als KI gewählt.")
                else:
                    st.markdown("Du hast das **rechte** Bild als KI gewählt.")
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
        "is_correct": is_correct
    })

    if st.session_state.current_idx + 1 < len(st.session_state.quiz_data):
        st.session_state.current_idx += 1
    else:
        st.session_state.finished = True
    st.rerun()

if __name__ == "__main__":
    main()
