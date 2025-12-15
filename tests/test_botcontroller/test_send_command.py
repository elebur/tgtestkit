async def test_default_args(mock_controller):
    await mock_controller.send_command("/python")

    mock_controller.client.send_message.assert_awaited_once_with(
        mock_controller._target_peer, "/python",
    )


async def test_without_leading_slash(mock_controller):
    await mock_controller.send_command("python")

    mock_controller.client.send_message.assert_awaited_once_with(
        mock_controller._target_peer, "/python",
    )


async def test_with_iterable_args(mock_controller):
    await mock_controller.send_command("/python", ("-m", "venv", ".venv"))

    mock_controller.client.send_message.assert_awaited_once_with(
        mock_controller._target_peer, "/python -m venv .venv",
    )


async def test_with_str_args(mock_controller):
    await mock_controller.send_command("/support", "ticket new open")

    mock_controller.client.send_message.assert_awaited_once_with(
        mock_controller._target_peer, "/support ticket new open",
    )


async def test_with_peer(mock_controller, fake_user):
    mock_controller.client.get_entity.return_value = fake_user
    await mock_controller.send_command("/python", peer=fake_user.username)

    mock_controller.client.get_entity.assert_awaited_once_with(fake_user.username)
    mock_controller.client.send_message.assert_awaited_once_with(
        fake_user, "/python",
    )


async def test_with_add_bot_name(mock_controller):
    await mock_controller.send_command("/python", add_bot_name=True)

    mock_controller.client.send_message.assert_awaited_once_with(
        mock_controller._target_peer,
        f"/python@{mock_controller.target_username}",
    )


async def test_with_all_args_set(mock_controller, fake_user):
    mock_controller.client.get_entity.return_value = fake_user
    await mock_controller.send_command(
        "/python",
        ("arg1", "arg2", "arg3"),
        peer="jhondoe",
        add_bot_name=True,
    )

    mock_controller.client.send_message.assert_awaited_once_with(
        fake_user,
        f"/python@{mock_controller.target_username} arg1 arg2 arg3",
    )
