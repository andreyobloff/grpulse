from dataclasses import dataclass
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from secrets import token_hex


class AuthenticationError(Exception):
    pass


class AccessDeniedError(Exception):
    status_code = 403


@dataclass(frozen=True)
class User:
    user_id: str
    login: str
    password_hash: str
    role: str = "operator"


@dataclass(frozen=True)
class ProtectedStationRecord:
    record_id: str
    station_id: str
    owner_user_id: str
    district: str
    sensor_type: str
    value: float


class PasswordHasher:
    def __init__(
        self,
        iterations: int = 120_000,
        algorithm: str = "sha256",
    ) -> None:
        self.iterations = iterations
        self.algorithm = algorithm

    def hash_password(
        self,
        password: str,
    ) -> str:
        salt = token_hex(16)
        digest = pbkdf2_hmac(
            self.algorithm,
            password.encode("utf-8"),
            salt.encode("utf-8"),
            self.iterations,
        ).hex()

        return f"{self.algorithm}"

    def verify_password(
        self,
        password: str,
        stored_hash: str,
    ) -> bool:
        algorithm, iterations_raw, salt, expected_digest = stored_hash.split("$")
        iterations = int(iterations_raw)

        actual_digest = pbkdf2_hmac(
            algorithm,
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        ).hex()

        return compare_digest(actual_digest, expected_digest)


class AuthService:
    def __init__(
        self,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        self.password_hasher = password_hasher or PasswordHasher()
        self.users_by_login: dict[str, User] = {}

    def register_user(
        self,
        user_id: str,
        login: str,
        password: str,
        role: str = "operator",
    ) -> User:
        self._validate_login(login)
        self._validate_password(password)

        if login in self.users_by_login:
            raise AuthenticationError("User already exists")

        user = User(
            user_id=user_id,
            login=login,
            password_hash=self.password_hasher.hash_password(password),
            role=role,
        )

        self.users_by_login[login] = user

        return user

    def authenticate(
        self,
        login: str,
        password: str,
    ) -> User:
        user = self.users_by_login.get(login)

        if user is None:
            raise AuthenticationError("Invalid login or password")

        if not self.password_hasher.verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid login or password")

        return user

    def _validate_login(
        self,
        login: str,
    ) -> None:
        if len(login.strip()) < 3:
            raise AuthenticationError("Login is too short")

    def _validate_password(
        self,
        password: str,
    ) -> None:
        if len(password) < 8:
            raise AuthenticationError("Password is too short")

        if password.isalpha() or password.isdigit():
            raise AuthenticationError("Password is too weak")


class AccessControlService:
    def get_user_records(
        self,
        current_user: User,
        records: list[ProtectedStationRecord],
    ) -> list[ProtectedStationRecord]:
        if current_user.role == "admin":
            return records

        return [
            record
            for record in records
            if record.owner_user_id == current_user.user_id
        ]

    def get_record_by_id(
        self,
        current_user: User,
        records: list[ProtectedStationRecord],
        record_id: str,
    ) -> ProtectedStationRecord:
        record = self._find_record(records, record_id)

        if current_user.role == "admin":
            return record

        if record.owner_user_id != current_user.user_id:
            raise AccessDeniedError("Access denied")

        return record

    def _find_record(
        self,
        records: list[ProtectedStationRecord],
        record_id: str,
    ) -> ProtectedStationRecord:
        for record in records:
            if record.record_id == record_id:
                return record

        raise ValueError("Record not found")


def load_security_demo_records() -> list[ProtectedStationRecord]:
    return [
        ProtectedStationRecord(
            record_id="REC-001",
            station_id="MSK-001",
            owner_user_id="USR-001",
            district="ЦАО",
            sensor_type="pm25",
            value=18.4,
        ),
        ProtectedStationRecord(
            record_id="REC-002",
            station_id="MSK-002",
            owner_user_id="USR-002",
            district="САО",
            sensor_type="co2",
            value=1150.0,
        ),
        ProtectedStationRecord(
            record_id="REC-003",
            station_id="MSK-003",
            owner_user_id="USR-001",
            district="ЮВАО",
            sensor_type="pm10",
            value=180.0,
        ),
    ]
