import streamlit as st
import os
import random
import mysql.connector
from datetime import datetime

# Konfiguration der Pfade (relativ zum Skript-Verzeichnis)
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

    # 3. Anzeige der Auswertung am Ende
    if st.session_state.finished:
        st.balloons()
        st.header("Quiz beendet!")

        st.metric("Dein Score", f"{st.session_state.score} von {len(st.session_state.quiz_data)} richtig erkannt")

        if st.button("Quiz neu starten"):
            del st.session_state.quiz_data
            st.rerun()
        return

    # 4. Quiz-Loop
    idx = st.session_state.current_idx
    pair = st.session_state.quiz_data[idx]

    st.progress(idx / len(st.session_state.quiz_data))
    st.subheader(f"Bildpaar {idx + 1} von {len(st.session_state.quiz_data)}")

    col1, col2 = st.columns(2)

    # Bestimmen, welches Bild in welche Spalte kommt
    if pair['ki_on_left']:
        left_img, right_img = pair['ki'], pair['human']
        left_is_ki = True
    else:
        left_img, right_img = pair['human'], pair['ki']
        left_is_ki = False

    with col1:
        st.image(left_img, use_container_width=True)
        if st.button("Das linke Bild ist KI 👈", key=f"btn_l_{idx}"):
            check_answer(left_is_ki)

    with col2:
        st.image(right_img, use_container_width=True)
        if st.button("Das rechte Bild ist KI 👉", key=f"btn_r_{idx}"):
            check_answer(not left_is_ki)

def check_answer(is_correct):
    if is_correct:
        st.session_state.score += 1

    if st.session_state.current_idx + 1 < len(st.session_state.quiz_data):
        st.session_state.current_idx += 1
    else:
        st.session_state.finished = True
    st.rerun()

if __name__ == "__main__":
    main()
