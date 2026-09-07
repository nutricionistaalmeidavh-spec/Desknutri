from nutridesktop.ui_kit.theme import DEFAULT_THEME, THEMES, build_stylesheet, get_theme


def test_premium_rose_theme_is_the_product_default():
    assert DEFAULT_THEME == "premium-rose-healthcare"
    theme = get_theme()
    assert theme.key == DEFAULT_THEME
    assert theme.accent == "#A84770"
    assert theme.sidebar_bg == "#FFFCFD"
    assert theme.composition_lean == "#9A7895"
    assert theme.composition_fat == "#F3C35B"
    assert "professional-data-clinic" in THEMES


def test_theme_stylesheet_keeps_legacy_and_semantic_contracts():
    stylesheet = build_stylesheet(get_theme(DEFAULT_THEME))
    for contract in (
        "QWidget#sidebar",
        "QFrame#card",
        "QLabel#pageTitle",
        "QPushButton[primary=\"true\"]",
        "QFrame#comparisonCard",
    ):
        assert contract in stylesheet
