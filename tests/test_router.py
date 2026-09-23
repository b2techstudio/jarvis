from app.core.command_router import CommandRouter, RouteKind


def test_routes_minimal_scenario() -> None:
    router = CommandRouter()
    assert router.route("Ouvre la calculatrice.").tool_name == "open_application"
    volume = router.route("Mets le volume à 30 %.")
    assert volume.tool_name == "set_volume"
    assert volume.arguments["level"] == 30
    assert router.route("Quelle heure est-il ?").tool_name == "current_datetime"
    note = router.route("Note que je dois acheter du café.")
    assert note.tool_name == "add_note"
    assert note.arguments["text"] == "je dois acheter du café"
    assert router.route("Quelles sont mes dernières notes ?").tool_name == "list_notes"


def test_routes_conversation_to_ai() -> None:
    route = CommandRouter().route("Explique-moi ce qu'est Docker")
    assert route.kind is RouteKind.CONVERSATION


def test_confirmation_answers() -> None:
    router = CommandRouter()
    assert router.route("oui", awaiting_confirmation=True).kind is RouteKind.CONFIRM
    assert router.route("non", awaiting_confirmation=True).kind is RouteKind.CANCEL

