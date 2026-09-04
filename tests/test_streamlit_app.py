from pathlib import Path

from streamlit.testing.v1 import AppTest

SAMPLE_LIVE = [
    {
        "profileUrl": "https://example.com/alice.png",
        "display": "AliceLive",
        "twitch": "alicelive",
        "online": True,
        "game": "ZEVENT",
        "viewersAmount": {"number": 1200},
        "donationAmount": {"number": 350.0},
        "donationUrl": "https://example.com/donate/alice",
    },
    {
        "profileUrl": "https://example.com/bob.png",
        "display": "BobOffline",
        "twitch": "boboffline",
        "online": False,
        "game": "Offline",
        "viewersAmount": {"number": 0},
        "donationAmount": {"number": 75.0},
        "donationUrl": "https://example.com/donate/bob",
    },
]


def make_app():
    app = AppTest.from_file(
        Path(__file__).parents[1] / "streamlit_app.py", default_timeout=10
    )
    app.session_state["live"] = SAMPLE_LIVE
    app.session_state["globalDonationUrl"] = "https://example.com/donate"
    app.session_state["donationAmount"] = {"formatted": "425 €"}
    app.session_state["viewersCount"] = {"formatted": "1 200"}
    app.session_state["event_status"] = (
        "Direct",
        "green",
        ":material/circle:",
    )
    return app.run()


def test_live_view_is_selected_by_default():
    app = make_app()

    assert not app.exception
    assert app.segmented_control[0].value == "En direct"
    assert len(app.dataframe[0].value) == 1
    assert app.dataframe[0].value.iloc[0]["display"] == "AliceLive"


def test_all_view_and_search_filter_streamers():
    app = make_app()

    app.segmented_control[0].set_value("Tous").run()
    assert not app.exception
    assert len(app.dataframe[0].value) == 2

    app.text_input[0].set_value("Bob").run()
    assert not app.exception
    assert len(app.dataframe[0].value) == 1
    assert app.dataframe[0].value.iloc[0]["display"] == "BobOffline"


def test_game_filter_limits_streamers():
    app = make_app()

    app.selectbox[1].select("ZEVENT").run()

    assert not app.exception
    assert len(app.dataframe[0].value) == 1
    assert app.dataframe[0].value.iloc[0]["display"] == "AliceLive"


def test_empty_search_shows_feedback():
    app = make_app()

    app.text_input[0].set_value("inconnu").run()

    assert not app.exception
    assert app.info
    assert not app.dataframe
