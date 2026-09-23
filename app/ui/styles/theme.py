STYLESHEET = """
QWidget {
    background-color: #090d12;
    color: #e8f7fb;
    font-family: "Segoe UI";
    font-size: 14px;
}
QMainWindow { background-color: #090d12; }
QFrame#panel, QDialog { background-color: #101820; border: 1px solid #1b3440; border-radius: 12px; }
QLabel#title { color: #70e7ff; font-size: 25px; font-weight: 600; letter-spacing: 2px; }
QLabel#state { color: #70e7ff; font-size: 16px; }
QLabel#muted { color: #71838d; font-size: 12px; }
QLabel#good { color: #63e6be; }
QLabel#bad { color: #ff8787; }
QLineEdit, QTextEdit, QListWidget, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #0b1118;
    border: 1px solid #244653;
    border-radius: 8px;
    padding: 8px;
    selection-background-color: #167a91;
}
QPushButton {
    background-color: #123441;
    border: 1px solid #2aaec9;
    border-radius: 9px;
    color: #dffaff;
    min-height: 34px;
    padding: 4px 14px;
}
QPushButton:hover { background-color: #195064; }
QPushButton:pressed { background-color: #0e829c; }
QPushButton#mic { border-radius: 30px; min-width: 60px; min-height: 60px; font-size: 24px; }
QPushButton#mic[recording="true"] { background-color: #7f2636; border-color: #ff6b81; }
QCheckBox { spacing: 8px; }
QSlider::groove:horizontal { height: 5px; background: #203640; border-radius: 2px; }
QSlider::handle:horizontal { background: #70e7ff; width: 14px; margin: -5px 0; border-radius: 7px; }
"""

