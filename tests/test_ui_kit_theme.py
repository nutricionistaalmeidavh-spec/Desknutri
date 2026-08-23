from nutridesktop.ui_kit.theme import DEFAULT_THEME, THEMES, build_stylesheet, get_theme


def test_dark_professional_theme_is_the_product_default():
    assert DEFAULT_THEME == "professional-data-clinic"
    assert get_theme().key == DEFAULT_THEME
    assert "professional-data-clinic" in THEMES


def test_theme_stylesheet_keeps_legacy_and_semantic_contracts():
    stylesheet = build_stylesheet(get_theme(DEFAULT_THEME))
    for contract in ("QWidget#sidebar", "QFrame#card", "QLabel#pageTitle", "QPushButton[primary=\"true\"]"):
        assert contract in stylesheet
