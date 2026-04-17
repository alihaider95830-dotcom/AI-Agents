import { authApi, redirectToLogin } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

jest.mock("@/lib/api", () => ({
  AUTH_TOKEN_STORAGE_KEY: "ai-report-token",
  redirectToLogin: jest.fn(),
  authApi: {
    login: jest.fn(),
    register: jest.fn(),
    me: jest.fn(),
  },
}));

const mockedAuthApi = authApi as jest.Mocked<typeof authApi>;
const mockedRedirectToLogin = redirectToLogin as jest.Mock;

const mockUser = {
  id: "user-1",
  email: "ali@example.com",
  full_name: "Ali Haider",
  tier: "pro" as const,
  credits: 48,
};

describe("authStore", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.localStorage.clear();
    useAuthStore.setState({
      user: null,
      token: null,
      isLoading: false,
      isAuthenticated: false,
    });
  });

  it("test_login_stores_token", async () => {
    mockedAuthApi.login.mockResolvedValue({ access_token: "token-123" });
    mockedAuthApi.me.mockResolvedValue(mockUser);

    await useAuthStore.getState().login("ali@example.com", "password123");

    expect(useAuthStore.getState().token).toBe("token-123");
    expect(window.localStorage.getItem("ai-report-token")).toBe("token-123");
    expect(useAuthStore.getState().user).toEqual(mockUser);
  });

  it("test_logout_clears_state", () => {
    window.localStorage.setItem("ai-report-token", "token-123");
    useAuthStore.setState({
      user: mockUser,
      token: "token-123",
      isAuthenticated: true,
    });

    useAuthStore.getState().logout();

    expect(useAuthStore.getState().user).toBeNull();
    expect(useAuthStore.getState().token).toBeNull();
    expect(window.localStorage.getItem("ai-report-token")).toBeNull();
    expect(mockedRedirectToLogin).toHaveBeenCalled();
  });

  it("test_initAuth_fetches_user", async () => {
    window.localStorage.setItem("ai-report-token", "persisted-token");
    mockedAuthApi.me.mockResolvedValue(mockUser);

    await useAuthStore.getState().initAuth();

    expect(mockedAuthApi.me).toHaveBeenCalledTimes(1);
    expect(useAuthStore.getState().token).toBe("persisted-token");
    expect(useAuthStore.getState().user).toEqual(mockUser);
  });
});
