"""
Universal GUI Functions
"""

from PySide2.QtGui import QIcon, QPalette

from functions import func


def style(app, icon="assets/cyckei.png", highlight="orange"):
    app.setStyle("Fusion")
    app.setWindowIcon(QIcon(func.find_path(icon)))
    palette = QPalette()
    palette.setColor(QPalette.ButtonText, func.teal)
    app.setPalette(palette)
