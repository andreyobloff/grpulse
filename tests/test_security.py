from src.security import (
    AccessControlService,
    AccessDeniedError,
    AuthService,
    AuthenticationError,
    load_security_demo_records,
)


def test_password_is_stored_as_hash() -> None:
    auth_service = AuthService()

    user = auth_service.register_user(
        user_id="USR-001",
        login="operator",
        password="StrongPass123",
    )

    assert user.password_hash != "StrongPass123"
    assert "StrongPass123" not in user.password_hash
    assert user.password_hash.startswith("sha256$")


def test_user_can_authenticate_with_valid_password() -> None:
    auth_service = AuthService()

    auth_service.register_user(
        user_id="USR-001",
        login="operator",
        password="StrongPass123",
    )

    user = auth_service.authenticate(
        login="operator",
        password="StrongPass123",
    )

    assert user.user_id == "USR-001"


def test_invalid_password_is_rejected() -> None:
    auth_service = AuthService()

    auth_service.register_user(
        user_id="USR-001",
        login="operator",
        password="StrongPass123",
    )

    try:
        auth_service.authenticate(
            login="operator",
            password="WrongPass123",
        )
    except AuthenticationError:
        assert True
    else:
        assert False


def test_user_sees_only_own_records() -> None:
    auth_service = AuthService()
    access_control = AccessControlService()
    records = load_security_demo_records()

    user = auth_service.register_user(
        user_id="USR-001",
        login="operator",
        password="StrongPass123",
    )

    user_records = access_control.get_user_records(user, records)

    assert len(user_records) == 2
    assert all(record.owner_user_id == "USR-001" for record in user_records)


def test_access_to_another_user_record_is_denied() -> None:
    auth_service = AuthService()
    access_control = AccessControlService()
    records = load_security_demo_records()

    user = auth_service.register_user(
        user_id="USR-001",
        login="operator",
        password="StrongPass123",
    )

    try:
        access_control.get_record_by_id(
            current_user=user,
            records=records,
            record_id="REC-002",
        )
    except AccessDeniedError as error:
        assert error.status_code == 403
    else:
        assert False


def test_admin_can_access_all_records() -> None:
    auth_service = AuthService()
    access_control = AccessControlService()
    records = load_security_demo_records()

    admin = auth_service.register_user(
        user_id="USR-ADMIN",
        login="admin",
        password="AdminPass123",
        role="admin",
    )

    admin_records = access_control.get_user_records(admin, records)

    assert len(admin_records) == 3


if __name__ == "__main__":
    test_password_is_stored_as_hash()
    test_user_can_authenticate_with_valid_password()
    test_invalid_password_is_rejected()
    test_user_sees_only_own_records()
    test_access_to_another_user_record_is_denied()
    test_admin_can_access_all_records()
    print("GreenPulse security measures tests passed")
