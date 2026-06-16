import pytest
import jwt


class TestLogin:
    """登录接口自动化测试"""

    @pytest.fixture
    def credentials(self):
        return {"username": "emilys", "password": "emilyspass"}

    # ── 正向场景 ──

    @pytest.mark.smoke
    @pytest.mark.positive
    def test_login_success(self, client, credentials):
        """正确凭证登录 → 200，返回 accessToken"""
        rsp = client.post("/auth/login", json=credentials)
        data = rsp.json()

        assert rsp.status_code == 200
        assert "accessToken" in data
        assert len(data["accessToken"]) > 0
        assert data["username"] == credentials["username"]

    @pytest.mark.positive
    def test_login_returns_valid_jwt(self, client, credentials):
        """accessToken 是合法 JWT"""
        rsp = client.post("/auth/login", json=credentials)
        data = rsp.json()

        decoded = jwt.decode(data["accessToken"], options={"verify_signature": False})
        assert decoded["id"] == 1
        assert decoded["username"] == credentials["username"]

    @pytest.mark.structure
    def test_login_response_structure(self, client, credentials):
        """返回 JSON 包含全部必要字段"""
        rsp = client.post("/auth/login", json=credentials)
        data = rsp.json()

        for field in ["accessToken", "refreshToken", "id", "username",
                       "email", "firstName", "lastName", "gender", "image"]:
            assert field in data, f"缺少字段: {field}"

    # ── 异常场景 ──

    @pytest.mark.negative
    def test_login_missing_password(self, client, credentials):
        """缺少 password → 400"""
        rsp = client.post("/auth/login", json={"username": credentials["username"]})

        assert rsp.status_code == 400

    @pytest.mark.negative
    def test_login_missing_username(self, client, credentials):
        """缺少 username → 400"""
        rsp = client.post("/auth/login", json={"password": credentials["password"]})

        assert rsp.status_code == 400

    @pytest.mark.negative
    def test_login_empty_body(self, client):
        """空请求体 → 400"""
        rsp = client.post("/auth/login", json={})

        assert rsp.status_code == 400

    @pytest.mark.negative
    def test_login_wrong_password(self, client, credentials):
        """错误密码 → 400"""
        rsp = client.post("/auth/login",
                          json={**credentials, "password": "wrongpass"})
        data = rsp.json()

        assert rsp.status_code == 400
        assert "Invalid credentials" in data["message"]

    @pytest.mark.negative
    @pytest.mark.parametrize("payload,expected_msg", [
        ({"username": "noexist", "password": "x"}, "Invalid credentials"),
        ({"username": "", "password": "x"}, "Username and password required"),
        ({"username": "emilys", "password": ""}, "Username and password required"),
    ])
    def test_login_invalid_scenarios(self, client, payload, expected_msg):
        """参数化异常：未注册 / 空用户名 / 空密码"""
        rsp = client.post("/auth/login", json=payload)
        data = rsp.json()

        assert rsp.status_code == 400
        assert expected_msg in data["message"]
