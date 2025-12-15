async def test_with_default_peer(controller):
    await controller.start()

    actual_commands = [c.command for c in await controller.get_commands_list()]
    commands_to_check = ("newbot", "mybots", "token", "cancel", "deletebot", "editgame")

    assert controller.client.is_connected()
    assert controller._target_peer.username == "BotFather"
    assert all(c in actual_commands for c in commands_to_check)


async def test_with_custom_peer(controller):
    await controller.start()

    actual_commands = [c.command for c in await controller.get_commands_list("wallet")]

    assert controller.client.is_connected()
    assert actual_commands == ["start"]
